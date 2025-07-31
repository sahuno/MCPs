#!/usr/bin/env Rscript

# Generic Genomic Segment Annotation Tool
# Author: Samuel Ahuno
# Description: Annotates BED3/BED6/BED12 files with genomic features

suppressPackageStartupMessages({
  library(optparse)
  library(tidyverse)
  library(annotatr)
  library(GenomicRanges)
  library(data.table)
  library(ggplot2)
})

# Command line options
option_list <- list(
  make_option(c("-i", "--input"), type="character", default=NULL,
              help="Input BED file(s). Single file or comma-separated list, or directory path", metavar="character"),
  make_option(c("--pattern"), type="character", default="*.bed",
              help="File pattern when input is directory [default= %default]", metavar="character"),
  make_option(c("--batch"), action="store_true", default=FALSE,
              help="Enable batch mode for multiple files"),
  make_option(c("--combine"), action="store_true", default=FALSE,
              help="Create combined analysis across all input files"),
  make_option(c("-o", "--output"), type="character", default="annotation_results",
              help="Output directory [default= %default]", metavar="character"),
  make_option(c("-g", "--genome"), type="character", default=NULL,
              help="Genome build (hg19, hg38, mm9, mm10, dm3, dm6, rn4, rn5, rn6)", metavar="character"),
  make_option(c("-n", "--name"), type="character", default="sample",
              help="Sample/condition name [default= %default]", metavar="character"),
  make_option(c("--cpg"), action="store_true", default=TRUE,
              help="Include CpG annotations [default]"),
  make_option(c("--genic"), action="store_true", default=TRUE,
              help="Include genic annotations [default]"),
  make_option(c("--plots"), action="store_true", default=TRUE,
              help="Generate visualization plots [default]"),
  make_option(c("--formats"), type="character", default="png,pdf,svg",
              help="Output plot formats (comma-separated) [default= %default]", metavar="character")
)

opt_parser <- OptionParser(option_list=option_list,
                          description="Annotate genomic segments from BED files",
                          epilogue="Example: Rscript annotate_genomic_segments.R -i input.bed -g hg38 -o results")
opt <- parse_args(opt_parser)

# Validate required arguments
if (is.null(opt$input)) {
  print_help(opt_parser)
  stop("Input BED file must be specified with -i/--input", call.=FALSE)
}

if (is.null(opt$genome)) {
  cat("Available genome builds:\n")
  cat("  hg19 - Human (GRCh37)\n")
  cat("  hg38 - Human (GRCh38)\n")
  cat("  mm9  - Mouse (NCBI37)\n")
  cat("  mm10 - Mouse (GRCh38)\n")
  cat("  dm3  - Drosophila (BDGP Release 5)\n")
  cat("  dm6  - Drosophila (BDGP Release 6)\n")
  cat("  rn4  - Rat (RGSC 3.4)\n")
  cat("  rn5  - Rat (RGSC 5.0)\n")
  cat("  rn6  - Rat (RGSC 6.0)\n")
  stop("Genome build must be specified with -g/--genome", call.=FALSE)
}

# Validate genome build
valid_genomes <- c("hg19", "hg38", "mm9", "mm10", "dm3", "dm6", "rn4", "rn5", "rn6")
if (!opt$genome %in% valid_genomes) {
  stop(paste("Invalid genome build. Valid options:", paste(valid_genomes, collapse=", ")), call.=FALSE)
}

# Validate input file exists
if (!file.exists(opt$input)) {
  stop(paste("Input file does not exist:", opt$input), call.=FALSE)
}

# Parse output formats
plot_formats <- strsplit(opt$formats, ",")[[1]]
valid_formats <- c("png", "pdf", "svg")
if (!all(plot_formats %in% valid_formats)) {
  stop(paste("Invalid plot format. Valid options:", paste(valid_formats, collapse=", ")), call.=FALSE)
}

# Create output directory structure
dir.create(opt$output, recursive = TRUE, showWarnings = FALSE)
for (fmt in plot_formats) {
  dir.create(file.path(opt$output, fmt), recursive = TRUE, showWarnings = FALSE)
}

cat("=== Genomic Segment Annotation Tool ===\n")
cat("Input file:", opt$input, "\n")
cat("Genome build:", opt$genome, "\n")
cat("Output directory:", opt$output, "\n")
cat("Sample name:", opt$name, "\n")
cat("Plot formats:", paste(plot_formats, collapse=", "), "\n\n")

# Function to resolve input files
resolve_input_files <- function(input_path, pattern="*.bed") {
  if (dir.exists(input_path)) {
    # Input is a directory
    files <- list.files(input_path, pattern=glob2rx(pattern), full.names=TRUE, recursive=FALSE)
    if (length(files) == 0) {
      stop(paste("No files matching pattern", pattern, "found in directory:", input_path))
    }
    cat("Found", length(files), "files in directory:", input_path, "\n")
    return(files)
  } else if (grepl(",", input_path)) {
    # Comma-separated list of files
    files <- trimws(strsplit(input_path, ",")[[1]])
    missing_files <- files[!file.exists(files)]
    if (length(missing_files) > 0) {
      stop(paste("Files not found:", paste(missing_files, collapse=", ")))
    }
    cat("Processing", length(files), "specified files\n")
    return(files)
  } else if (file.exists(input_path)) {
    # Single file
    cat("Processing single file:", input_path, "\n")
    return(input_path)
  } else {
    stop(paste("Input path does not exist:", input_path))
  }
}

# Function to generate sample name from file path
generate_sample_name <- function(file_path, base_name=NULL) {
  if (!is.null(base_name) && base_name != "sample") {
    return(paste0(base_name, "_", tools::file_path_sans_ext(basename(file_path))))
  } else {
    return(tools::file_path_sans_ext(basename(file_path)))
  }
}

# Function to detect BED format and read file
read_bed_file <- function(file_path) {
  # Read first line to detect format
  first_line <- readLines(file_path, n=1)
  
  # Skip header lines starting with #
  skip_lines <- 0
  con <- file(file_path, "r")
  while (TRUE) {
    line <- readLines(con, n=1)
    if (length(line) == 0 || !startsWith(line, "#")) {
      break
    }
    skip_lines <- skip_lines + 1
  }
  close(con)
  
  # Read the file
  if (skip_lines > 0) {
    df <- fread(file_path, skip=skip_lines, sep="\t")
  } else {
    df <- fread(file_path, sep="\t")
  }
  
  # Detect BED format based on number of columns
  ncols <- ncol(df)
  
  if (ncols >= 12) {
    # BED12 format
    colnames(df)[1:12] <- c("chrom", "chromStart", "chromEnd", "name", "score", "strand",
                           "thickStart", "thickEnd", "itemRgb", "blockCount", 
                           "blockSizes", "blockStarts")
    bed_format <- "BED12"
  } else if (ncols >= 6) {
    # BED6 format
    colnames(df)[1:6] <- c("chrom", "chromStart", "chromEnd", "name", "score", "strand")
    bed_format <- "BED6"
  } else if (ncols >= 3) {
    # BED3 format
    colnames(df)[1:3] <- c("chrom", "chromStart", "chromEnd")
    bed_format <- "BED3"
  } else {
    stop("Invalid BED format. Must have at least 3 columns (chrom, start, end)")
  }
  
  # Ensure required columns are present and properly formatted
  df$chrom <- as.character(df$chrom)
  df$chromStart <- as.numeric(df$chromStart)
  df$chromEnd <- as.numeric(df$chromEnd)
  
  # Add standard GenomicRanges column names for compatibility
  # Ensure we have both sets of column names to avoid ambiguity
  df$seqnames <- df$chrom
  df$start <- df$chromStart + 1  # Convert 0-based to 1-based coordinates (BED is 0-based)
  df$end <- df$chromEnd
  
  # Handle strand information if available
  if ("strand" %in% colnames(df)) {
    # Replace "." with "*" for GenomicRanges compatibility
    df$strand[df$strand == "."] <- "*"
  }
  
  cat("Detected", bed_format, "format with", ncol(df), "columns\n")
  cat("Loaded", nrow(df), "genomic regions\n\n")
  
  return(list(data=df, format=bed_format))
}

# Function to add annotatr annotations
add_annotations <- function(df, genome_build, include_cpg=TRUE, include_genic=TRUE) {
  cat("Building annotations for", genome_build, "...\n")
  
  # Create GenomicRanges object preserving all metadata
  # Explicitly specify seqnames, start, end columns to avoid ambiguity
  tryCatch({
    gr <- makeGRangesFromDataFrame(df, 
                                   seqnames.field = "seqnames",
                                   start.field = "start", 
                                   end.field = "end",
                                   keep.extra.columns = TRUE)
  }, error = function(e) {
    # Fallback: try with standard BED column names
    tryCatch({
      gr <- makeGRangesFromDataFrame(df, 
                                     seqnames.field = "chrom",
                                     start.field = "chromStart", 
                                     end.field = "chromEnd",
                                     keep.extra.columns = TRUE)
    }, error = function(e2) {
      # Final fallback: ensure we have the right column names
      temp_df <- df
      # Force standard column names for the first 3 columns
      colnames(temp_df)[1:3] <- c("seqnames", "start", "end")
      gr <- makeGRangesFromDataFrame(temp_df, keep.extra.columns = TRUE)
    })
  })
  
  # Build the complete annotation list at once
  annotation_types <- c()
  
  # Add CpG annotations
  if (include_cpg) {
    cpg_types <- c(
      paste0(genome_build, "_cpgs"),
      paste0(genome_build, "_cpg_islands"),
      paste0(genome_build, "_cpg_shores"),
      paste0(genome_build, "_cpg_shelves"),
      paste0(genome_build, "_cpg_inter")
    )
    annotation_types <- c(annotation_types, cpg_types)
  }
  
  # Add genic annotations
  if (include_genic) {
    genic_types <- c(
      paste0(genome_build, "_genes_promoters"),
      paste0(genome_build, "_genes_5UTRs"),
      paste0(genome_build, "_genes_exons"),
      paste0(genome_build, "_genes_introns"),
      paste0(genome_build, "_genes_3UTRs"),
      paste0(genome_build, "_genes_intergenic"),
      paste0(genome_build, "_genes_1to5kb"),
      paste0(genome_build, "_genes_cds")
    )
    annotation_types <- c(annotation_types, genic_types)
  }
  
  # Build all annotations at once - this is the correct way
  all_annotations <- build_annotations(
    genome = genome_build,
    annotations = annotation_types
  )
  
  # Annotate regions
  cat("Annotating", length(gr), "regions...\n")
  annotated_gr <- annotate_regions(
    regions = gr,
    annotations = all_annotations,
    ignore.strand = TRUE,
    quiet = FALSE
  )
  
  cat("Annotation complete!\n")
  cat("Number of annotated regions:", length(annotated_gr), "\n")
  
  # Add diagnostic information
  if (length(annotated_gr) > 0) {
    cat("Sample of annotation types found:\n")
    annotation_summary <- table(annotated_gr$annot.type)
    print(head(annotation_summary, 10))
    cat("\n")
  } else {
    cat("WARNING: No annotated regions found!\n\n")
  }
  
  return(annotated_gr)
}

# Function to create visualization plots
create_plots <- function(annotated_gr, sample_name, output_dir, plot_formats) {
  if (length(annotated_gr) == 0) {
    cat("No annotated regions found. Skipping plots.\n")
    return()
  }
  
  cat("Creating visualization plots...\n")
  
  # Create annotation plot
  for (fmt in plot_formats) {
    tryCatch({
      plot_obj <- plot_annotation(
        annotated_regions = annotated_gr,
        plot_title = paste('Genomic Annotations:', sample_name),
        x_label = 'Genomic Features',
        y_label = 'Count'
      )
      
      # Apply formatting guidelines with better visibility
      plot_obj <- plot_obj + 
        theme_minimal() +
        theme(
          text = element_text(family = "Arial", size = 14),
          plot.title = element_text(face = "bold", size = 16),
          axis.text.x = element_text(size = 12, angle = 45, hjust = 1, color = "black"),
          axis.text.y = element_text(size = 12, color = "black"),
          axis.title.x = element_text(face = "bold", size = 14, color = "black"),
          axis.title.y = element_text(face = "bold", size = 14, color = "black"),
          axis.line = element_line(color = "black", linewidth = 0.5),
          axis.ticks = element_line(color = "black", linewidth = 0.5),
          panel.grid.major = element_line(color = "grey90", linewidth = 0.2),
          panel.grid.minor = element_blank(),
          legend.text = element_text(size = 12),
          legend.title = element_text(face = "bold", size = 14)
        )
      
      # Save plot with optimized dimensions
      filename <- file.path(output_dir, fmt, paste0(sample_name, "_annotations.", fmt))
      
      if (fmt == "png") {
        ggsave(filename, plot_obj, width = 14, height = 10, dpi = 300, units = "in")
      } else if (fmt == "pdf") {
        ggsave(filename, plot_obj, width = 14, height = 10, units = "in", device = cairo_pdf)
      } else if (fmt == "svg") {
        ggsave(filename, plot_obj, width = 14, height = 10, units = "in")
      }
      
      cat("Saved", fmt, "plot:", filename, "\n")
    }, error = function(e) {
      cat("Warning: Could not create", fmt, "plot:", e$message, "\n")
    })
  }
}

# Function to create combined analysis across multiple files
create_combined_analysis <- function(all_results, output_dir, plot_formats) {
  if (length(all_results) < 2) {
    cat("Skipping combined analysis - only one file processed\n")
    return()
  }
  
  cat("Creating combined analysis across", length(all_results), "files...\n")
  
  # Combine all annotated data
  combined_data <- list()
  for (sample_name in names(all_results)) {
    df <- as.data.frame(all_results[[sample_name]])
    df$sample <- sample_name
    combined_data[[sample_name]] <- df
  }
  combined_df <- bind_rows(combined_data)
  
  # Save combined data
  combined_file <- file.path(output_dir, "combined_annotations.tsv")
  fwrite(combined_df, combined_file, sep = "\t")
  cat("Saved combined data:", combined_file, "\n")
  
  # Create combined summary plot
  if (nrow(combined_df) > 0) {
    for (fmt in plot_formats) {
      tryCatch({
        # Plot 1: Annotation counts by sample
        count_plot <- combined_df %>%
          group_by(sample, annot.type) %>%
          summarise(count = n(), .groups = "drop") %>%
          ggplot(aes(x = annot.type, y = count, fill = sample)) +
          geom_bar(stat = "identity", position = "dodge") +
          theme_minimal() +
          theme(
            text = element_text(family = "Arial", size = 12),
            plot.title = element_text(face = "bold", size = 14),
            axis.text.x = element_text(size = 10, angle = 45, hjust = 1, color = "black"),
            axis.text.y = element_text(size = 10, color = "black"),
            axis.title = element_text(face = "bold", size = 12, color = "black"),
            axis.line = element_line(color = "black", linewidth = 0.5),
            axis.ticks = element_line(color = "black", linewidth = 0.5),
            legend.position = "bottom"
          ) +
          labs(
            title = "Genomic Annotations Comparison Across Samples",
            x = "Annotation Type",
            y = "Count",
            fill = "Sample"
          )
        
        filename <- file.path(output_dir, fmt, paste0("combined_comparison.", fmt))
        
        if (fmt == "png") {
          ggsave(filename, count_plot, width = 16, height = 10, dpi = 300, units = "in")
        } else if (fmt == "pdf") {
          ggsave(filename, count_plot, width = 16, height = 10, units = "in", device = cairo_pdf)
        } else if (fmt == "svg") {
          ggsave(filename, count_plot, width = 16, height = 10, units = "in")
        }
        
        cat("Saved combined", fmt, "plot:", filename, "\n")
      }, error = function(e) {
        cat("Warning: Could not create combined", fmt, "plot:", e$message, "\n")
      })
    }
    
    # Create summary statistics table
    summary_stats <- combined_df %>%
      group_by(sample) %>%
      summarise(
        total_regions = n(),
        unique_annotations = n_distinct(annot.type),
        mean_width = mean(width, na.rm = TRUE),
        median_width = median(width, na.rm = TRUE),
        .groups = "drop"
      )
    
    summary_file <- file.path(output_dir, "combined_summary_stats.tsv")
    fwrite(summary_stats, summary_file, sep = "\t")
    cat("Saved combined summary:", summary_file, "\n")
    
    # Print summary
    cat("\n=== Combined Analysis Summary ===\n")
    print(summary_stats)
  }
}

# Main execution
tryCatch({
  # Resolve input files
  input_files <- resolve_input_files(opt$input, opt$pattern)
  
  # Process files
  all_results <- list()
  
  for (i in seq_along(input_files)) {
    input_file <- input_files[i]
    sample_name <- generate_sample_name(input_file, opt$name)
    
    cat("\n=== Processing file", i, "of", length(input_files), "===\n")
    cat("File:", input_file, "\n")
    cat("Sample name:", sample_name, "\n")
    
    # Read input BED file
    bed_data <- read_bed_file(input_file)
    input_df <- bed_data$data
    
    # Add annotations
    annotated_gr <- add_annotations(input_df, opt$genome, opt$cpg, opt$genic)
    
    # Store results for combined analysis
    all_results[[sample_name]] <- annotated_gr
    
    # Convert to data frame for output
    annotated_df <- as.data.frame(annotated_gr)
    
    # Create sample-specific output directory if multiple files
    if (length(input_files) > 1) {
      sample_output_dir <- file.path(opt$output, sample_name)
      dir.create(sample_output_dir, recursive = TRUE, showWarnings = FALSE)
      for (fmt in plot_formats) {
        dir.create(file.path(sample_output_dir, fmt), recursive = TRUE, showWarnings = FALSE)
      }
    } else {
      sample_output_dir <- opt$output
    }
    
    # Save annotated results
    output_file <- file.path(sample_output_dir, paste0(sample_name, "_annotated.tsv"))
    fwrite(annotated_df, output_file, sep = "\t")
    cat("Saved annotated results:", output_file, "\n")
    
    # Create plots if requested
    if (opt$plots) {
      create_plots(annotated_gr, sample_name, sample_output_dir, plot_formats)
    }
    
    # Create summary statistics
    if (length(annotated_gr) > 0) {
      summary_stats <- annotated_df %>%
        group_by(annot.type) %>%
        summarise(
          count = n(),
          mean_width = mean(width, na.rm = TRUE),
          median_width = median(width, na.rm = TRUE),
          .groups = "drop"
        ) %>%
        arrange(desc(count))
      
      summary_file <- file.path(sample_output_dir, paste0(sample_name, "_summary.tsv"))
      fwrite(summary_stats, summary_file, sep = "\t")
      cat("Saved summary statistics:", summary_file, "\n")
      
      # Print summary to console
      cat("\n=== Annotation Summary for", sample_name, "===\n")
      print(summary_stats)
    }
  }
  
  # Create combined analysis if requested and multiple files processed
  if (opt$combine && length(input_files) > 1) {
    create_combined_analysis(all_results, opt$output, plot_formats)
  }
  
  cat("\n=== All files processed successfully! ===\n")
  cat("Results saved to:", opt$output, "\n")
  if (length(input_files) > 1) {
    cat("Individual results in sample-specific subdirectories\n")
    if (opt$combine) {
      cat("Combined analysis in main output directory\n")
    }
  }
  
}, error = function(e) {
  cat("Error:", e$message, "\n")
  quit(status = 1)
})
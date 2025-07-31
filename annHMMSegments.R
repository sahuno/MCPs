# Extended DMR Annotation Script for All Merged Results
# This script processes all DMR segmentation files and generates clearly labeled outputs

# Load required libraries
library(tidyverse)
library(annotatr)
library(GenomicRanges)
library(data.table)
library(ggplot2)

# Create output directory structure
output_base <- "/data1/greenbab/projects/triplicates_epigenetics_diyva/committee_meeting1/outputs/qstat_group_only/dmr_tri_epi_results/dmr_annotations"
dir.create(output_base, recursive = TRUE, showWarnings = FALSE)

# Function to categorize Cohen's h effect size (using lower bound)
categorize_cohen_h <- function(cohen_h_value) {
  abs_h <- abs(cohen_h_value)
  case_when(
    abs_h < 0.2 ~ "negligible",
    abs_h < 0.5 ~ "small",
    abs_h < 0.8 ~ "medium",
    TRUE ~ "large"
  )
}

# Function to determine hyper/hypo methylation (using effect_size instead of cohen_h)
determine_methylation_status <- function(effect_size) {
  ifelse(effect_size > 0, "hyper", "hypo")
}

# Function to load and annotate a single segmentation file
load_and_annotate_segmentation <- function(file_path, condition_name) {
  df <- fread(file_path, sep = "\t")
  names(df) <- gsub("^#", "", names(df))
  
  df$condition <- condition_name
  df$cohen_category <- categorize_cohen_h(df$cohen_h_low)
  df$methylation_status <- determine_methylation_status(df$effect_size)
  
  return(df)
}

# Function to add annotatr annotations
add_annotatr_annotations <- function(df, gname="mm10", genome = "mm10") {
  gr <- makeGRangesFromDataFrame(df, keep.extra.columns = TRUE)
  
  # Build annotations
  cpg_annotations <- build_annotations(
    genome = gname,
    annotations = c(
      paste0(gname, "_cpgs"),
      paste0(gname, "_cpg_islands"),
      paste0(gname, "_cpg_shores"),
      paste0(gname, "_cpg_shelves"),
      paste0(gname, "_cpg_inter")
    )
  )
  
  genic_annotations <- build_annotations(
    genome = gname,
    annotations = c(
      paste0(gname, "_genes_promoters"),
      paste0(gname, "_genes_5UTRs"),
      paste0(gname, "_genes_exons"),
      paste0(gname, "_genes_introns"),
      paste0(gname, "_genes_3UTRs"),
      paste0(gname, "_genes_intergenic"),
      paste0(gname, "_genes_1to5kb"),
      paste0(gname, "_genes_cds")
    )
  )
  
  all_annotations <- c(cpg_annotations, genic_annotations)
  
  # Annotate regions
  annotated_gr_all <- annotate_regions(
    regions = gr,
    annotations = all_annotations,
    ignore.strand = TRUE,
    quiet = FALSE
  )
  
  annotated_gr_cpgs <- annotate_regions(
    regions = gr,
    annotations = cpg_annotations,
    ignore.strand = TRUE,
    quiet = FALSE
  )
  
  annotated_gr_genic <- annotate_regions(
    regions = gr,
    annotations = genic_annotations,
    ignore.strand = TRUE,
    quiet = FALSE
  )
  
  # Convert to data frames
  annotated_df <- as.data.frame(annotated_gr_cpgs)
  annotated_df_genic <- as.data.frame(annotated_gr_genic)
  
  # Add region IDs
  df$region_id <- paste(df$seqnames, df$start, df$end, sep = "_")
  annotated_df$region_id <- paste(annotated_df$seqnames, annotated_df$start, annotated_df$end, sep = "_")
  annotated_df_genic$region_id <- paste(annotated_df_genic$seqnames, annotated_df_genic$start, annotated_df_genic$end, sep = "_")
  
  return(list(
    all_gr = annotated_gr_all,
    gr_cpgs = annotated_gr_cpgs,
    gr_genic = annotated_gr_genic,
    df_cpgs = annotated_df,
    df_genic = annotated_df_genic
  ))
}

# Function to create comprehensive plots for each condition
create_condition_plots <- function(annotations, condition_name, output_dir) {
  # Create condition-specific output directory
  condition_dir <- file.path(output_dir, condition_name)
  dir.create(condition_dir, recursive = TRUE, showWarnings = FALSE)
  
  # Filter for significant effects
  gr_filtered_cpgs <- annotations$gr_cpgs[
    str_detect(annotations$gr_cpgs$cohen_category, "medium|large|small")
  ]
  
  gr_filtered_genic <- annotations$gr_genic[
    str_detect(annotations$gr_genic$cohen_category, "medium|large|small")
  ]
  
  # Plot 1: CpG annotations
  if (length(gr_filtered_cpgs) > 0) {
    cpg_plot <- plot_annotation(
      annotated_regions = gr_filtered_cpgs,
      plot_title = paste('DMR Segments in CpG Regions:', condition_name),
      x_label = 'CpG Annotations',
      y_label = 'Count'
    )
    
    cpg_plot <- cpg_plot + theme(text = element_text(size = 18))
    
    ggsave(
      filename = file.path(condition_dir, paste0(condition_name, "_cpg_annotations.pdf")),
      plot = cpg_plot,
      width = 10,
      height = 6
    )
  }
  
  # Plot 2: Genic annotations
  if (length(gr_filtered_genic) > 0) {
    genic_plot <- plot_annotation(
      annotated_regions = gr_filtered_genic,
      plot_title = paste('DMR Segments in Genic Regions:', condition_name),
      x_label = 'Genic Annotations',
      y_label = 'Count'
    )
    
    genic_plot <- genic_plot + theme(text = element_text(size = 18))
    
    ggsave(
      filename = file.path(condition_dir, paste0(condition_name, "_genic_annotations.pdf")),
      plot = genic_plot,
      width = 10,
      height = 6
    )
  }
  
  # Plot 3: Effect size vs Cohen's h by genic region
  if (length(gr_filtered_genic) > 0) {
    gr_filtered_genic_dt <- gUtils::gr2dt(gr_filtered_genic)
    gr_filtered_genic_dt$annot_type <- gsub("mm10_genes_", "", gr_filtered_genic_dt$annot.type)
    
    effect_plot <- ggplot(gr_filtered_genic_dt, aes(x = effect_size, y = cohen_h_low, color = methylation_status)) +
      geom_point() +
      geom_hline(yintercept = c(-0.8, -0.5, -0.2, 0.2, 0.5, 0.8), 
                 linetype = "dashed", 
                 color = "gray50", 
                 alpha = 0.7) +
      annotate("text", x = -Inf, y = 0.2, label = "small", 
               hjust = -0.1, vjust = -0.5, size = 3.5, color = "gray40") +
      annotate("text", x = -Inf, y = 0.5, label = "medium", 
               hjust = -0.1, vjust = -0.5, size = 3.5, color = "gray40") +
      annotate("text", x = -Inf, y = 0.8, label = "large", 
               hjust = -0.1, vjust = -0.5, size = 3.5, color = "gray40") +
      labs(
        title = paste(condition_name, "DMRs: Effect Size vs Cohen's h (lower bound) by Genic Region"),
        x = "Effect Size",
        y = "Cohen's h (lower bound)"
      ) +
      facet_wrap(~annot_type, scales = "fixed") +
      theme_minimal() +
      theme(text = element_text(size = 16), legend.position = "bottom") +
      scale_color_manual(values = c("hyper" = "#E63946", "hypo" = "#457B9D"))
    
    ggsave(
      filename = file.path(condition_dir, paste0(condition_name, "_effect_vs_cohen_by_region.pdf")),
      plot = effect_plot,
      width = 12,
      height = 8
    )
    
    # Save data table
    fwrite(
      gr_filtered_genic_dt,
      file = file.path(condition_dir, paste0(condition_name, "_genic_dmr_data.tsv")),
      sep = "\t"
    )
  }
  
  # Plot 4: Cohen's h (lower bound) distribution
  cohen_dist_plot <- ggplot(data.frame(cohen_h_low = annotations$gr_cpgs$cohen_h_low), 
                            aes(x = cohen_h_low)) +
    geom_histogram(bins = 50, fill = "#457B9D", alpha = 0.7, color = "black") +
    geom_vline(xintercept = c(-0.8, -0.5, -0.2, 0.2, 0.5, 0.8), 
               linetype = "dashed", color = "red", alpha = 0.5) +
    labs(
      title = paste(condition_name, ": Cohen's h (lower bound) Distribution"),
      x = "Cohen's h (lower bound)",
      y = "Count"
    ) +
    theme_minimal() +
    theme(text = element_text(size = 16))
  
  ggsave(
    filename = file.path(condition_dir, paste0(condition_name, "_cohen_h_distribution.pdf")),
    plot = cohen_dist_plot,
    width = 8,
    height = 6
  )
  
  return(list(
    cpg_plot = cpg_plot,
    genic_plot = genic_plot,
    effect_plot = effect_plot,
    cohen_dist_plot = cohen_dist_plot
  ))
}

# Main processing function
process_all_dmr_conditions <- function(base_dir, output_dir) {
  # Find all segmentation files
  seg_files <- list.files(
    base_dir,
    pattern = "segmentation.bed.gz$",
    recursive = TRUE,
    full.names = TRUE
  )
  
  if (length(seg_files) == 0) {
    stop("No segmentation files found in the specified directory")
  }
  
  # Process each condition
  all_results <- list()
  all_plots <- list()
  
  for (file_path in seg_files) {
    # Extract condition name
    condition <- basename(dirname(file_path))
    
    cat("Processing:", condition, "\n")
    
    # Load and annotate
    df <- load_and_annotate_segmentation(file_path, condition)
    message("Loaded segmentation data for: ", condition)
    
    # Add annotations
    annotations <- add_annotatr_annotations(df, gname="mm10", genome = "mm10")
    message("Added annotations for: ", condition)
    
    # Create plots
    plots <- create_condition_plots(annotations, condition, output_dir)
    
    # Store results
    all_results[[condition]] <- annotations
    all_plots[[condition]] <- plots
    
    # Save individual condition results
    saveRDS(
      annotations,
      file = file.path(output_dir, condition, paste0(condition, "_annotations.rds"))
    )
  }
  
  return(list(results = all_results, plots = all_plots))
}

# Create combined summary plots
create_summary_plots <- function(all_results, output_dir) {
  # Combine all data
  combined_data <- list()
  
  for (condition in names(all_results)) {
    df <- as.data.frame(all_results[[condition]]$gr_cpgs)
    df$condition <- condition
    combined_data[[condition]] <- df
  }
  
  combined_df <- bind_rows(combined_data)
  
  # Summary plot 1: Cohen's h (lower bound) by condition
  cohen_summary <- ggplot(combined_df, aes(x = cohen_h_low, fill = condition)) +
    geom_histogram(bins = 50, alpha = 0.7, position = "identity") +
    facet_wrap(~condition, scales = "free_y", ncol = 1) +
    theme_minimal() +
    theme(text = element_text(size = 16)) +
    labs(
      title = "Cohen's h (lower bound) Distribution Across All Conditions",
      x = "Cohen's h (lower bound)",
      y = "Count"
    ) +
    scale_fill_manual(values = c("CKI_vs_DMSO" = "#457B9D", 
                                "QSTAT_vs_DMSO" = "#F1FAEE", 
                                "QSTAT_CKI_vs_DMSO" = "#E63946"))
  
  ggsave(
    filename = file.path(output_dir, "all_conditions_cohen_h_distribution.pdf"),
    plot = cohen_summary,
    width = 10,
    height = 12
  )
  
  # Summary plot 2: Effect categories by condition
  category_summary <- combined_df %>%
    group_by(condition, cohen_category, methylation_status) %>%
    summarise(count = n(), .groups = "drop") %>%
    ggplot(aes(x = cohen_category, y = count, fill = methylation_status)) +
    geom_bar(stat = "identity", position = "dodge") +
    facet_wrap(~condition, scales = "free_y") +
    theme_minimal() +
    theme(text = element_text(size = 16), 
          axis.text.x = element_text(angle = 45, hjust = 1)) +
    labs(
      title = "DMR Effect Size Categories by Condition",
      x = "Effect Size Category",
      y = "Count",
      fill = "Methylation Status"
    ) +
    scale_fill_manual(values = c("hyper" = "#E63946", "hypo" = "#457B9D"))
  
  ggsave(
    filename = file.path(output_dir, "all_conditions_effect_categories.pdf"),
    plot = category_summary,
    width = 12,
    height = 8
  )
  
  # Create summary statistics table
  summary_stats <- combined_df %>%
    group_by(condition) %>%
    summarise(
      total_dmrs = n(),
      hyper_count = sum(methylation_status == "hyper"),
      hypo_count = sum(methylation_status == "hypo"),
      mean_cohen_h_low = mean(cohen_h_low, na.rm = TRUE),
      median_cohen_h_low = median(cohen_h_low, na.rm = TRUE),
      large_effects = sum(cohen_category == "large"),
      medium_effects = sum(cohen_category == "medium"),
      small_effects = sum(cohen_category == "small"),
      negligible_effects = sum(cohen_category == "negligible"),
      .groups = "drop"
    )
  
  fwrite(
    summary_stats,
    file = file.path(output_dir, "all_conditions_summary_statistics.tsv"),
    sep = "\t"
  )
  
  return(list(
    cohen_summary = cohen_summary,
    category_summary = category_summary,
    summary_stats = summary_stats
  ))
}

# Check overlaps with repeat regions
check_repeat_overlaps <- function(all_results, repeat_bed_path, output_dir) {
  # Load repeat regions
  if (file.exists(repeat_bed_path)) {
    dfrep <- read_tsv(repeat_bed_path, 
                     col_names = c("chrom", "start", "end", "name", "score", "strand"))
    gr_repeats <- makeGRangesFromDataFrame(dfrep, keep.extra.columns = TRUE)
    
    overlap_results <- list()
    
    for (condition in names(all_results)) {
      # Get significant DMRs
      gr_dmrs <- all_results[[condition]]$gr_genic[
        str_detect(all_results[[condition]]$gr_genic$cohen_category, "medium|large")
      ]
      
      if (length(gr_dmrs) > 0) {
        # Find overlaps
        overlaps <- findOverlaps(gr_dmrs, gr_repeats)
        
        if (length(overlaps) > 0) {
          dmr_with_repeats <- gr_dmrs[queryHits(overlaps)]
          repeat_regions <- gr_repeats[subjectHits(overlaps)]
          
          # Create overlap data frame
          overlap_df <- data.frame(
            dmr_chr = seqnames(dmr_with_repeats),
            dmr_start = start(dmr_with_repeats),
            dmr_end = end(dmr_with_repeats),
            cohen_h_low = dmr_with_repeats$cohen_h_low,
            effect_size = dmr_with_repeats$effect_size,
            methylation_status = dmr_with_repeats$methylation_status,
            repeat_name = repeat_regions$name,
            repeat_chr = seqnames(repeat_regions),
            repeat_start = start(repeat_regions),
            repeat_end = end(repeat_regions)
          )
          
          overlap_results[[condition]] <- overlap_df
          
          # Save overlaps
          fwrite(
            overlap_df,
            file = file.path(output_dir, condition, 
                           paste0(condition, "_dmr_repeat_overlaps.tsv")),
            sep = "\t"
          )
        }
      }
    }
    
    # Create summary of overlaps
    if (length(overlap_results) > 0) {
      overlap_summary <- bind_rows(overlap_results, .id = "condition") %>%
        group_by(condition) %>%
        summarise(
          total_overlaps = n(),
          unique_repeats = n_distinct(repeat_name),
          hyper_overlaps = sum(methylation_status == "hyper"),
          hypo_overlaps = sum(methylation_status == "hypo"),
          .groups = "drop"
        )
      
      fwrite(
        overlap_summary,
        file = file.path(output_dir, "repeat_overlap_summary.tsv"),
        sep = "\t"
      )
    }
  } else {
    warning("Repeat bed file not found: ", repeat_bed_path)
  }
}

# Main execution
cat("Starting extended DMR annotation analysis\n")
cat("Output directory:", output_base, "\n\n")

# Process all conditions
base_dir <- "/data1/greenbab/projects/triplicates_epigenetics_diyva/committee_meeting1/outputs/qstat_group_only/dmr_tri_epi_results/dmr_merged"
results <- process_all_dmr_conditions(base_dir, output_base)

# Create summary plots
cat("\nCreating summary plots across all conditions\n")
summary_plots <- create_summary_plots(results$results, output_base)

# Check repeat overlaps
cat("\nChecking overlaps with repeat regions\n")
repeat_bed <- "/data1/greenbab/projects/triplicates_epigenetics_diyva/RNA/rerun_RNASeq_11032025/REP_locusSpecDE/outputs/repeats_DNAme_RNA/all_results_repeats_promoter.bed"
check_repeat_overlaps(results$results, repeat_bed, output_base)

# Save all results
saveRDS(results, file.path(output_base, "all_dmr_annotation_results.rds"))

# Print summary
cat("\n\nAnalysis complete!\n")
cat("Results saved to:", output_base, "\n")
cat("\nDirectory structure:\n")
cat("- Main output directory:", output_base, "\n")
cat("- Condition-specific subdirectories:\n")
for (condition in names(results$results)) {
  cat("  -", condition, "/\n")
}
cat("\nKey output files:\n")
cat("- all_conditions_cohen_h_distribution.pdf\n")
cat("- all_conditions_effect_categories.pdf\n")
cat("- all_conditions_summary_statistics.tsv\n")
cat("- all_dmr_annotation_results.rds\n")
cat("- Per condition: *_cpg_annotations.pdf, *_genic_annotations.pdf, *_effect_vs_cohen_by_region.pdf\n")

# Create a README for the output directory
readme_content <- "# DMR Annotation Results

## Directory Structure
- Each condition has its own subdirectory with condition-specific analyses
- Combined analyses are in the main directory

## File Naming Convention
- {condition}_cpg_annotations.pdf - CpG region annotations
- {condition}_genic_annotations.pdf - Genic region annotations  
- {condition}_effect_vs_cohen_by_region.pdf - Effect size vs Cohen's h (lower bound) plots
- {condition}_cohen_h_distribution.pdf - Cohen's h (lower bound) distribution
- {condition}_genic_dmr_data.tsv - Annotated DMR data
- {condition}_dmr_repeat_overlaps.tsv - DMRs overlapping with repeat regions

## Summary Files
- all_conditions_cohen_h_distribution.pdf - Combined Cohen's h (lower bound) distributions
- all_conditions_effect_categories.pdf - Effect size categories by condition
- all_conditions_summary_statistics.tsv - Summary statistics table
- repeat_overlap_summary.tsv - Summary of DMR-repeat overlaps
- all_dmr_annotation_results.rds - Complete R data object with all results

## Conditions Analyzed
"

for (condition in names(results$results)) {
  readme_content <- paste0(readme_content, "- ", condition, "\n")
}

writeLines(readme_content, file.path(output_base, "README.md"))

cat("\nREADME.md created in output directory\n")
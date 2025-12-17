# Dashboard Documentation - Visual Overview

## What You're Getting

### 📄 Main Documentation File
**Location:** `docs/source/tutorials/dashboard-guide.rst`

A comprehensive 433-line tutorial explaining every aspect of the SimPM dashboard:

```
Dashboard Guide
├─ Overview
├─ Starting the Dashboard
├─ Dashboard Layout
│  ├─ Overview Section
│  │  ├─ Environment Metric
│  │  └─ Run ID Selector
│  ├─ Simulation Runs Section
│  │  ├─ Table Tab
│  │  ├─ Statistics Tab
│  │  ├─ Histogram Tab
│  │  └─ Box Plot Tab
│  ├─ Navigation Section
│  ├─ Entities View
│  │  ├─ Entity Selector
│  │  ├─ Schedule Section
│  │  │  ├─ Table Preview
│  │  │  ├─ Statistics
│  │  │  ├─ Time series
│  │  │  ├─ Histogram
│  │  │  └─ Box plot
│  │  ├─ Waiting Log Section
│  │  │  ├─ Metric Selector
│  │  │  ├─ Statistics
│  │  │  ├─ Histogram
│  │  │  └─ Box plot
│  │  └─ Status Log Section
│  │     ├─ Time-weighted statistics
│  │     ├─ Time series
│  │     ├─ Histogram
│  │     └─ Box plot
│  ├─ Resources View
│  │  ├─ Resource Selector
│  │  ├─ Queue Log Section
│  │  │  ├─ Metric Selector
│  │  │  ├─ Statistics
│  │  │  ├─ Histogram
│  │  │  └─ Box plot
│  │  └─ Status Log Section
│  │     ├─ Time-weighted statistics
│  │     ├─ Time series
│  │     ├─ Histogram
│  │     └─ Box plot
│  └─ Activity View
│     ├─ Activity Table
│     └─ CSV Export
├─ Understanding the Visualizations
│  ├─ Time Series Graphs
│  ├─ Histograms
│  ├─ Box Plots
│  └─ Statistics Tables
├─ Exporting Data
├─ Tips & Troubleshooting
├─ Advanced Usage
└─ FAQ
```

## Information Architecture

### By User Role

**👶 Beginner**
→ "Starting the Dashboard" + "Overview Section" + "FAQ"

**📈 Analyst**
→ "Understanding the Visualizations" + "Advanced Usage" + "Exporting Data"

**🔧 Power User**
→ "Advanced Usage" + "FAQ" + linking to external analysis tools

### By Information Type

**Conceptual** (Understanding what each part means)
- Overview Section descriptions
- Waiting Log explanation
- Status Log explanation

**Procedural** (How to use it)
- Run ID Selector walkthrough
- Metric Selector usage
- CSV download instructions

**Reference** (Looking up specific features)
- Visualization guide
- Troubleshooting
- FAQ

**Practical** (Examples and tips)
- Tips & Troubleshooting
- Advanced Usage
- FAQ with real scenarios

## Content by Dashboard Component

### Overview & Run Selection
**Covers:**
- Environment metric display
- Single run vs. multiple runs
- Run selector dropdown behavior
- Run filter persistence

**Teaching:** Conceptual + Procedural

### Simulation Runs
**Covers:**
- Table preview with download
- Statistics (count, mean, median, min, max, std)
- Histogram interpretation
- Box plot reading
- Use cases for each visualization

**Teaching:** Procedural + Conceptual + Reference

### Navigation
**Covers:**
- Three main views: Entities, Resources, Activity
- View switching
- Filter persistence
- Summary metrics display

**Teaching:** Procedural

### Entities View
**Covers:**
- Entity selection
- **Schedule section**
  - What activities are logged
  - Duration statistics
  - Time series visualization
  - Histogram of durations
  - Spotting outliers
  
- **Waiting Log section**
  - What waiting means
  - Waiting duration analysis
  - Start/finish time tracking
  - Identifying bottlenecks
  
- **Status Log section**
  - Entity state tracking
  - Time-weighted statistics
  - Status transitions
  - Interpreting distributions

**Teaching:** Procedural + Conceptual

### Resources View
**Covers:**
- Resource selection
- **Queue Log section**
  - Queue tracking
  - Waiting duration analysis
  - Entity waiting patterns
  
- **Status Log section**
  - Resource utilization (in_use, idle)
  - Queue length tracking
  - Time-weighted utilization
  - Peak vs. average load

**Teaching:** Procedural + Conceptual

### Activity View
**Covers:**
- Unified event feed
- Activity sources (entity schedule, waiting, queue, environment)
- CSV export for external analysis
- Advanced filtering/analysis

**Teaching:** Procedural

## Visualization Teaching

### Time Series
- What it shows: Trends over time
- Interactive features: Zoom with slider, hover for values
- Use cases: Identifying when problems start, bottleneck evolution

### Histogram
- What it shows: Distribution and frequency
- Reading: X-axis = value, Y-axis = frequency
- Use cases: Variability assessment, identifying common vs. rare durations

### Box Plot
- What it shows: Quartiles and outliers
- Reading: Box = middle 50%, line = median, whiskers = range
- Use cases: Quick distribution summary, outlier detection

### Statistics Table
- What it shows: Exact numbers for distribution
- Metrics: Count, Mean, Median, Min, Max, Std
- Special: Time-weighted statistics for status logs

## Practical Guidance

### Troubleshooting
- No data in a section? → Check if log=True was used
- Empty visualizations? → Check for valid numeric values
- Slow performance? → Export to CSV and analyze locally

### Tips
- Multiple runs? → Use run selector to compare
- Identify bottlenecks? → Look for long waiting durations and high queue lengths
- Analyze variability? → Use histograms and standard deviation

### Advanced
- Custom metrics? → Log additional data with your simulation
- External analysis? → Export CSV and use pandas/matplotlib
- Deeper dives? → Combine dashboard insights with code analysis

## File Organization

```
SimPM/
├─ docs/
│  └─ source/
│     └─ tutorials/
│        ├─ index.rst (updated with dashboard-guide link)
│        ├─ dashboard-guide.rst (NEW - 433 lines)
│        ├─ hello-simpm.rst
│        ├─ schedule-risk.rst
│        ├─ resource-bottlenecks.rst
│        └─ images/
│           └─ dashboard/ (ready for 15 screenshots)
│
├─ DASHBOARD_SCREENSHOTS_GUIDE.txt (how to add images)
├─ SCREENSHOT_IMPLEMENTATION_CHECKLIST.md (detailed checklist)
├─ DASHBOARD_DOCS_SUMMARY.md (quick overview)
└─ IMPLEMENTATION_COMPLETE.txt (status report)
```

## Quick Reference for Each Section

| Section | Purpose | Key Info | Examples |
|---------|---------|----------|----------|
| **Overview** | Env info & run selection | Environment name, which run | Single run: 1 metric; Multiple: dropdown |
| **Simulation Runs** | Execution time stats | Count, mean, median, distribution | Consistency check, Monte Carlo analysis |
| **Entities View** | Per-entity analysis | Activities, waiting, status | Who works, how long, how long waiting |
| **Resources View** | Per-resource analysis | Queue, utilization, status | Bottleneck identification, capacity planning |
| **Activity View** | Event timeline | All events in one place | Sequence analysis, export for external tools |

## How Screenshots Will Be Integrated

Once captured (15 total images), they'll be placed:

1. **Overview section** (1 image)
2. **Simulation Runs** (4 images: table, stats, histogram, box plot)
3. **Navigation** (1 image)
4. **Entities > Schedule** (3 images: table, time series, histogram)
5. **Entities > Waiting Log** (1 image)
6. **Entities > Status Log** (1 image, optional)
7. **Resources > Queue Log** (1 image)
8. **Resources > Status Log** (2 images: time series, histogram)
9. **Activity View** (1 image)

Total: 15 images positioned throughout the guide

## Key Features Explained

### Metric Selectors
Many sections have dropdowns to choose what to visualize:
- **Entity Schedule:** Activity durations
- **Entity Waiting Log:** Waiting duration, start time, or finish time
- **Resource Queue:** Same as waiting log
- **Status Log:** in_use, idle, queue_length, or custom metrics

### CSV Downloads
Clickable download buttons appear in table previews:
- Full dataset exported as CSV
- For use in Excel, Python, R, etc.
- Includes all columns and rows (not just preview)

### Time-Weighted Statistics
Special to status logs (Resource Queue, Entity Status):
- Values weighted by duration
- Reflects % of time spent in each state
- Not simple average (which would give equal weight)
- Example: If busy 10 min, idle 90 min → 90% idle (time-weighted)

### Interactive Visualizations
Built on Plotly:
- Hover to see exact values
- Range slider for zooming (time series only)
- Click legend items to toggle series on/off
- Double-click to reset zoom

## Use Cases by Audience

**Project Manager**
- Check simulation times (Simulation Runs view)
- Identify bottlenecks (Resource Queue > Histogram)
- Spot variability (Histogram std dev)

**Engineer/Analyst**
- Detailed entity timelines (Entities > Schedule)
- Resource utilization breakdown (Resources > Status)
- Activity event sequence (Activity view)
- Export for further analysis (All CSV downloads)

**Researcher**
- Distribution analysis (All histograms and box plots)
- Time-weighted metrics (Status log statistics)
- Variance across runs (Multiple run comparison)
- Statistical rigor (External analysis with exported CSV)

**Operations Manager**
- Queue length trends (Resource Status > Time series)
- Utilization rates (Resource Status > Time-weighted stats)
- Peak demand periods (Resource Status > Time series zoom)
- Waiting time analysis (Queue Log > Histogram)

## Summary Statistics Explained

**Count:** How many data points

**Mean:** Average (sum ÷ count)

**Median:** Middle value (50th percentile, robust to outliers)

**Min:** Smallest value (best case)

**Max:** Largest value (worst case)

**Std:** Standard deviation (how spread out; higher = more variable)

**Time-Weighted:** Average accounting for duration at each value

---

## Ready to Use

This documentation is **production-ready**:
- ✅ Comprehensive coverage
- ✅ Well-structured
- ✅ Integrated into documentation system
- ✅ Can be built to HTML/PDF now
- ⏳ Screenshots can be added anytime

See **IMPLEMENTATION_COMPLETE.txt** for next steps!


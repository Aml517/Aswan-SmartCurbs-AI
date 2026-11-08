# Aswan SmartCurbs AI — ClickUp Free Plan Setup & Import Guide

This guide provides step-by-step instructions for importing the 16-week execution backlog into **ClickUp Free** and configuring your workspace for presentations to your professor.

---

## 1. File Artifacts Generated

The following production-ready planning files have been generated in your workspace:
1. **ClickUp Import CSV:** `Aswan_SmartCurbs_ClickUp_Import.csv`
2. **Master Excel Workbook:** `Aswan_SmartCurbs_16_Week_Sprint_Plan.xlsx` (Contains 6 tabs: Sprint Overview, Task Backlog, Team Allocation, Dependency Register, Risk Register, and Review Checklist)
3. **Setup Guide:** `Aswan_SmartCurbs_ClickUp_Setup_Guide.md`

---

## 2. ClickUp Free Plan Architecture & Constraints

ClickUp Free provides unlimited tasks, standard custom fields (100 uses on free tier, or standard free fields), and multiple views. To ensure 100% compliance without hitting Free plan paywalls:

- **Structure:** Create a single List named **`Aswan-SmartCurbs-Sprint-Plan`** inside your Space.
- **Sprint/Week Tracking:** Uses a standard Dropdown or Text Custom Field named **`Sprint`** (`Sprint 01` through `Sprint 16`) rather than ClickUp's premium Sprint Points/Sprint Folders.
- **Assignees:** Mapped to neutral placeholders **`Member A` through `Member F`** (can be mapped to real student emails in ClickUp if invited, or stored in a Custom Text Field `Team Role`).
- **Parent/Child:** Kept as flat tasks with explicit `Task ID` and `Parent Story` fields to ensure reliable CSV column mapping.

---

## 3. Step-by-Step CSV Import Instructions

### Step 1: Create your Space and List in ClickUp
1. Log into your ClickUp account.
2. In the left sidebar, click **Spaces** $ightarrow$ **+ New Space**.
3. Name the Space: `Aswan SmartCurbs AI`. Click **Next**.
4. Set default statuses:
   - `To Do` (Gray)
   - `In Progress` (Blue/Yellow)
   - `Done` (Green)
5. Under your new Space, create a new List named: **`16-Week Master Sprint Plan`**.

### Step 2: Open the CSV Importer
1. Click the Space settings cog $ightarrow$ **Settings** $ightarrow$ **Import / Export**.
2. Or click the `...` menu on the `16-Week Master Sprint Plan` List $ightarrow$ **Import** $ightarrow$ **Excel / CSV**.
3. Click **Upload File** and select `Aswan_SmartCurbs_ClickUp_Import.csv`.

### Step 3: Map CSV Columns to ClickUp Fields
Map the headers as follows:

| CSV Header | ClickUp Target Field | Field Type |
|---|---|---|
| `Task ID` | Custom Field: `Task ID` | Short Text |
| `Task Name` | **Task Name** | Standard Title (Required) |
| `Description` | **Description** | Standard Task Description |
| `Status` | **Status** | Standard Status (`To Do`, `In Progress`, `Done`) |
| `Priority` | **Priority** | Standard Priority (`Urgent`, `High`, `Normal`, `Low`) |
| `Sprint` | Custom Field: `Sprint` | Dropdown or Text (`Sprint 01` - `Sprint 16`) |
| `Assignee` | Custom Field: `Owner Placeholder` or Assignee | Text / User |
| `Estimated Time` | **Time Estimate** | Standard Time Estimate |
| `Component` | Custom Field: `Component` | Dropdown (`Backend`, `Frontend Driver`, `Frontend Admin`, `AI / Computer Vision`, `Integration & QA`, `DevOps & Security`) |
| `Acceptance Criteria` | Custom Field: `Acceptance Criteria` | Long Text |
| `Dependencies` | Custom Field: `Dependencies` | Short Text (e.g. `SW-0101`) |

4. Click **Complete Import**. ClickUp will import all 96 tasks within a few seconds.

---

## 4. Configuring Recommended Views for Your Professor

Once imported, configure these three views in the top navigation bar of your List:

### View A: "Sprint Roadmap" (Grouped by Sprint)
1. Add a **List View** and name it `16-Week Sprint Roadmap`.
2. Click **Group By** at the top right $ightarrow$ Select `Custom Field: Sprint`.
3. The view will automatically organize into 16 clean collapsible sprint sections (`Sprint 01` through `Sprint 16`).
4. Display columns: `Task ID`, `Assignee`, `Priority`, `Time Estimate`, `Status`.

### View B: "Kanban Board" (Grouped by Status)
1. Add a **Board View** and name it `Execution Kanban`.
2. Ensure columns are grouped by **Status** (`To Do` $ightarrow$ `In Progress` $ightarrow$ `Done`).
3. Click **Filter** $ightarrow$ `Sprint = Sprint 01` (or current active sprint) to focus during weekly sprint reviews.

### View C: "Team Workload" (Grouped by Assignee)
1. Add a **Table View** or **Board View** and name it `Team Allocation (6 Members)`.
2. Click **Group By** $ightarrow$ Select `Assignee` (Member A through Member F).
3. This clearly proves to the professor that workload is balanced (~30h/week per student) across Frontend, Backend, AI, QA, and DevOps.

---

## 5. Weekly Sprint Review Protocol

To run your weekly sprint review with your professor:
1. Open the `Execution Kanban` view for the target week.
2. Walk through the **Sprint Review Checklist** tab of `Aswan_SmartCurbs_16_Week_Sprint_Plan.xlsx`.
3. Show the concrete test evidence (e.g. Stage test scorecard, live UI demonstration, or CSV export).
4. Review risks from the **Risk Register** and transition verified tasks to `Done`.

---
name: Aswan Smart Curbs Admin
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#44474e'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#75777f'
  outline-variant: '#c5c6cf'
  surface-tint: '#4e5e81'
  primary: '#031635'
  on-primary: '#ffffff'
  primary-container: '#1a2b4b'
  on-primary-container: '#8293b8'
  inverse-primary: '#b6c6ef'
  secondary: '#006a61'
  on-secondary: '#ffffff'
  secondary-container: '#86f2e4'
  on-secondary-container: '#006f66'
  tertiary: '#08172a'
  on-tertiary: '#ffffff'
  tertiary-container: '#1e2c3f'
  on-tertiary-container: '#8593ab'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#b6c6ef'
  on-primary-fixed: '#081b3a'
  on-primary-fixed-variant: '#364768'
  secondary-fixed: '#89f5e7'
  secondary-fixed-dim: '#6bd8cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#d5e3fd'
  tertiary-fixed-dim: '#b9c7e0'
  on-tertiary-fixed: '#0d1c2f'
  on-tertiary-fixed-variant: '#3a485c'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  title-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-data:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 20px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style
The design system is engineered for a high-stakes municipal environment, where data density must coexist with immediate legibility. The aesthetic follows a **Corporate / Modern** direction with a heavy emphasis on **Information Architecture**.

The interface evokes a sense of "Civic Tech"—authoritative, stable, and transparent. It prioritizes the reduction of cognitive load for city operators managing real-time curb data. The visual language uses a systematic approach to whitespace and alignment to ensure that even complex datasets feel organized and actionable.

## Colors
The palette is anchored by **Dark Navy (#1A2B4B)** to establish institutional trust and authority. **Teal (#0D9488)** serves as the primary action color, providing a modern, "smart city" energy that contrasts against the traditional navy.

Surface colors utilize a tiered grayscale:
- **Background**: Very Light Gray (#F8FAFC) to define the workspace.
- **Surface**: Pure White (#FFFFFF) for primary content cards and data containers.
- **Text**: Slate Gray for instructional and body text, with a near-black Navy for high-contrast headings.

Semantic colors (Success, Warning, Danger) are strictly reserved for status indicators, occupancy thresholds, and system alerts to ensure they command attention when needed.

## Typography
**Inter** is utilized across all levels for its exceptional legibility in digital dashboards. 

- **Hierarchical Contrast**: Large headings use semi-bold and bold weights with slight negative letter-spacing to appear compact and professional.
- **Data Display**: For numerical data, tables, and occupancy counters, enable **tabular figures** (`tnum`) to ensure numbers align vertically for easier scanning.
- **Labels**: Small uppercase labels are used for metadata and table headers to distinguish them from interactive body content.

## Layout & Spacing
The layout follows a **Fluid Grid** model for the main dashboard area, with a **Fixed Sidebar** (280px) for global navigation.

- **Grid System**: A 12-column grid is used for desktop layouts. Cards typically span 3 columns for metrics, 6 columns for charts, and 12 columns for data tables.
- **Rhythm**: A 4px baseline shift ensures all components—from input fields to progress bars—maintain a consistent vertical cadence.
- **Density**: The spacing is "comfortable" rather than "compact" to allow the high-contrast typography to breathe, preventing the interface from feeling cluttered during peak data activity.

## Elevation & Depth
This design system uses **Tonal Layers** and **Ambient Shadows** to define the z-axis.

- **The Canvas**: The background is the lowest level (#F8FAFC).
- **The Containers**: Primary cards are raised using a "Soft Elevation" (Shadow: `0 4px 6px -1px rgba(15, 23, 42, 0.05), 0 2px 4px -2px rgba(15, 23, 42, 0.05)`).
- **Interactive States**: Buttons and active cards use a slightly deeper shadow on hover to indicate tactility.
- **Outlines**: A 1px border (#E2E8F0) is applied to all cards and containers even when shadowed, ensuring structural integrity in high-glare environments.

## Shapes
A **Rounded** (Level 2) shape language is applied to balance the professional navy-heavy palette with a modern, approachable feel. 

- **Standard Elements**: Buttons, Input Fields, and Checkboxes use `rounded-md` (8px).
- **Containers**: Dashboard cards and Modals use `rounded-lg` (12px) to clearly define content groupings.
- **Status Badges**: Use `rounded-full` (pill) to distinguish them from interactive buttons.

## Components
- **Primary Buttons**: Solid Navy (#1A2B4B) with white text. High-emphasis actions.
- **Secondary Buttons**: Outlined Teal (#0D9488). Used for secondary dashboard filters and exports.
- **Occupancy Progress Bars**: A custom component with a background of #E2E8F0 and a dynamic fill. Fill color transitions from Teal (0-70%) to Amber (71-90%) to Rose (91-100%).
- **Status Badges**: Subtle tinted backgrounds (e.g., 10% opacity of the semantic color) with 100% opacity text for high readability.
- **Data Tables**: Zebra-striping is avoided; instead, use 1px horizontal dividers (#F1F5F9). The header row is always a subtle gray (#F8FAFC) with uppercase Navy labels.
- **Metric Cards**: Large-format "Title-sm" labels with "Display-lg" values, featuring a small sparkline or trend indicator in the bottom-right corner.
- **Input Fields**: Focus state uses a 2px Teal border with a soft teal outer glow.
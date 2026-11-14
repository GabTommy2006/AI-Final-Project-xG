---
name: xG studio
description: Club editorial football analysis workspace
colors:
  pine: "#123D34"
  ivory: "#F5F5EF"
  ink: "#183B33"
  caption: "#466153"
  field: "#E8ECE5"
  lime: "#D6F285"
  focus: "#618522"
  pitch-line: "#A9C2B5"
  inverse-muted: "#D8E6DB"
  divider: "#BECBBF"
typography:
  display:
    fontFamily: "Manrope, sans-serif"
    fontSize: "2.6rem"
    fontWeight: 700
    letterSpacing: "-0.03em"
  display-mobile:
    fontFamily: "Manrope, sans-serif"
    fontSize: "2rem"
    fontWeight: 700
    letterSpacing: "-0.03em"
  result:
    fontFamily: "Manrope, sans-serif"
    fontSize: "3.4rem"
    fontWeight: 650
    letterSpacing: "-0.035em"
  brand:
    fontFamily: "Manrope, sans-serif"
    fontSize: "1.4rem"
    letterSpacing: "-0.03em"
  brand-caption:
    fontFamily: "Manrope, sans-serif"
    fontSize: "0.85rem"
  result-label:
    fontFamily: "Manrope, sans-serif"
    fontSize: "1rem"
rounded:
  signature: "12px"
spacing:
  unit: "1rem"
  band-inline: "1.25rem"
  desktop-top: "5rem"
  desktop-bottom: "3rem"
  mobile-top: "4.5rem"
components:
  brand-band:
    backgroundColor: "{colors.pine}"
    textColor: "{colors.ivory}"
    rounded: "{rounded.signature}"
    padding: "1rem 1.25rem"
  pitch:
    backgroundColor: "{colors.pine}"
    rounded: "{rounded.signature}"
    width: "100%"
  probability:
    textColor: "{colors.ink}"
    typography: "{typography.result}"
---

# Design System: xG studio

## Overview

**Creative North Star: "Club editorial"**

A quiet football analysis workspace with a dark pitch, readable probability and ordinary working controls. Manrope, pine and warm ivory connect the working screen to football annual reporting without adding ornamental dashboard furniture.

This is the system extracted from the implemented code and desktop/mobile captures. The direction remains a reversible styling assumption under delegated design work; neither user visual approval nor comp approval is recorded. Direction reference: seed:3f307c94f370302f.

**Key Characteristics:**
- Pine identity and pitch surfaces on warm ivory.
- A single sans-serif family with strong numerical hierarchy.
- Native Streamlit controls and navigation.
- Flat surfaces and restrained lime shot geometry.

## Colors

Muted greens carry the interface; lime identifies the selected shot and its goal opening.

### Primary
- **Pine:** identity band, pitch ground and primary interactive theme color.
- **Selected Lime:** shot marker, goal-mouth triangle and browser text selection.
- **Focus Olive:** keyboard focus outline color.

### Neutral
- **Warm Ivory:** page ground and inverse identity text.
- **Pine Ink:** main text.
- **Caption Green:** explanatory captions at full opacity.
- **Field Grey-Green:** native input surface theme.
- **Pitch Line:** pitch markings.
- **Inverse Muted:** pitch direction label and brand supporting text.
- **Divider Green:** probability row divider.

**The Selected Geometry Rule.** Lime identifies position and geometry; keep ordinary controls within the pine theme.

## Typography

**Display Font:** Manrope, with sans-serif fallback.
**Body Font:** Manrope, with sans-serif fallback.

The self-hosted variable face supplies weights 200–800. Display headings use tight tracking; the probability uses tabular figures so changing results keep a stable visual rhythm. Body, subheadings and widget labels inherit Streamlit typography rather than a separately defined custom scale.

### Hierarchy
- **Display:** main page title, using the display token and its mobile counterpart.
- **Headline:** native Streamlit subheadings with tracking of (-0.02em).
- **Result:** percentage, using the result token and tabular numerals.
- **Brand:** identity name and smaller supporting line.
- **Body / label:** native Streamlit text and control labels; result explanation uses the result-label token.

**The Stable Figures Rule.** Use tabular numerals for coordinate inputs and the headline probability.

## Layout

The main container is capped at (1240px), with desktop top and bottom padding from the spacing tokens. The working area uses Streamlit columns in a (1.5:1) ratio and its native large gap. The pitch and result share the wider column; numeric inputs and context fields occupy the narrower column.

At the custom (640px) breakpoint, page padding becomes (4.5rem 1rem 1rem) and the title uses the mobile token. Native Streamlit responsive behavior stacks the wider column, including its result, before the controls. The numeric input pair also stacks on the reviewed mobile capture; navigation wraps. The pitch scales with its container and preserves its (128:88) SVG viewBox ratio. Do not infer an additional grid breakpoint from the custom title breakpoint.

## Elevation & Depth

Custom surfaces have no box shadows. Pine and ivory establish surface separation; thin native control outlines and the result divider provide structure. Native Streamlit control states remain framework owned rather than a custom elevation system.

**The Flat Surface Rule.** Use color fields and fine boundaries for the documented custom surfaces.

## Shapes

The brand band and pitch use the signature radius. The SVG ground also has a (3-unit) corner radius in its own coordinate system. Native widgets retain Streamlit shapes; their internal radius is not promoted to a custom token.

## Components

### Identity band
A compact pine band with the name on the left and supporting text on the right. It uses flex alignment and the brand-band padding token. On mobile the supporting text has a maximum width of (135px), aligns right and wraps.

### Navigation and buttons
Segmented navigation uses the native Streamlit control, including selected and keyboard states. Reset spans its form column. The estimate download remains a native download button. Keep native behavior; no separate primary/ghost button palette is defined in app code.

### Inputs / Fields
Numeric x/y inputs and selectboxes use the Streamlit field theme. Coordinates use tabular numerals. Pitch selection and numeric input remain synchronized. The global focus-visible override changes outline color only; it does not supply a new outline width for native controls.

### Pitch position picker
The pitch is the distinctive working component. Its lime marker connects to the right-hand goal mouth through a triangle with (0.20) fill opacity. Click, drag and arrow keys select a position. Its keyboard focus is a (3px) olive outline with (3px) offset. Supporting instructions remain outside the graphic.

### Probability row
The large percentage and small xG label align on their baselines with a (1rem) gap. A thin divider and (1rem) bottom padding separate the number from its interpretation. The number remains textual and readable independently of color.

## Do's and Don'ts

### Do:
- **Do** retain Manrope across the interface and pitch labels.
- **Do** keep explanatory captions at full opacity.
- **Do** preserve both numeric and direct pitch position input.
- **Do** keep probability interpretation adjacent to the result.

### Don't:
- **Don't** replace native widget behavior with decorative control imitations.
- **Don't** turn lime into a general background for working controls.
- **Don't** infer visual approval from this implementation record.

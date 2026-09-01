# UI Responsiveness Testing Guide

## Overview

This document provides guidelines and procedures for testing the Ayurveda-AI frontend responsiveness across different devices, screen sizes, and orientations. The frontend is built with React + Vite and uses TailwindCSS for styling.

## Testing Objectives

- Ensure the application is fully functional on mobile devices (320px - 768px)
- Ensure the application is fully functional on tablet devices (768px - 1024px)
- Ensure the application is fully functional on desktop devices (1024px+)
- Verify touch interactions work correctly on mobile devices
- Verify keyboard navigation works correctly on desktop
- Ensure accessibility standards are met

## Breakpoints

The application uses the following TailwindCSS breakpoints:

- **sm**: 640px (small tablets)
- **md**: 768px (tablets)
- **lg**: 1024px (laptops)
- **xl**: 1280px (desktops)
- **2xl**: 1536px (large screens)

## Testing Tools

### Browser DevTools
Use Chrome DevTools Device Mode for responsive testing:
1. Open Chrome DevTools (F12)
2. Click on Device Toolbar (Ctrl+Shift+M)
3. Select device presets or enter custom dimensions

### Recommended Devices to Test

#### Mobile Devices
- iPhone SE (375px x 667px)
- iPhone 12 Pro (390px x 844px)
- iPhone 14 Pro Max (430px x 932px)
- Samsung Galaxy S21 (360px x 800px)
- Pixel 5 (393px x 851px)

#### Tablet Devices
- iPad (768px x 1024px)
- iPad Pro (1024px x 1366px)
- Samsung Galaxy Tab (800px x 1280px)

#### Desktop Resolutions
- 1366 x 768 (laptop)
- 1920 x 1080 (desktop)
- 2560 x 1440 (large desktop)

## Testing Checklist

### 1. Navigation

#### Mobile (< 768px)
- [ ] Hamburger menu is visible and functional
- [ ] Menu opens/closes smoothly
- [ ] Menu overlay covers entire screen
- [ ] Menu items are large enough for touch (min 44px height)
- [ ] Back button functionality works
- [ ] Navigation links are accessible via touch

#### Tablet (768px - 1024px)
- [ ] Navigation adapts to tablet layout
- [ ] Menu items are appropriately sized
- [ ] Touch targets are adequate
- [ ] No horizontal scrolling on navigation

#### Desktop (> 1024px)
- [ ] Full navigation bar is visible
- [ ] Hover states work correctly
- [ ] Dropdown menus function properly
- [ ] Keyboard navigation works (Tab, Enter, Escape)

### 2. Patient Dashboard

#### Mobile
- [ ] Patient cards stack vertically
- [ ] Patient information is readable
- [ ] Action buttons are accessible
- [ ] No horizontal scrolling
- [ ] Charts/graphs are readable (if present)
- [ ] Filters are accessible

#### Tablet
- [ ] Patient cards display in grid (2 columns)
- [ ] Information is well-spaced
- [ ] Touch interactions work smoothly

#### Desktop
- [ ] Patient cards display in grid (3-4 columns)
- [ ] Hover effects work
- [ ] Information density is appropriate

### 3. Doctor Dashboard

#### Mobile
- [ ] Consultation list is scrollable
- [ ] Consultation details are accessible
- [ ] Action buttons are touch-friendly
- [ ] Status indicators are visible
- [ ] Search functionality works

#### Tablet
- [ ] Consultation cards display appropriately
- [ ] Side-by-side layout works (if applicable)
- [ ] Quick actions are accessible

#### Desktop
- [ ] Full dashboard layout is utilized
- [ ] Multiple panels visible
- [ ] Advanced filters accessible

### 4. Consultation View

#### Mobile
- [ ] Consultation details are readable
- [ ] Notes section is accessible
- [ ] Document list is scrollable
- [ ] Zoom meeting link is clickable
- [ ] Status updates are easy to perform

#### Tablet
- [ ] Split view works (if implemented)
- [ ] Document preview is functional
- [ ] Notes editor is usable

#### Desktop
- [ ] Full consultation details visible
- [ ] Document preview side-by-side with details
- [ ] Rich text editor works
- [ ] Multiple tabs/panels accessible

### 5. AI Chat Interface

#### Mobile
- [ ] Chat input is accessible
- [ ] Message list scrolls properly
- [ ] Send button is touch-friendly
- [ ] Messages are readable
- [ ] Typing indicator is visible
- [ ] Source citations are clickable

#### Tablet
- [ ] Chat interface uses appropriate width
- [ ] Side panel (if any) is accessible

#### Desktop
- [ ] Chat interface uses full width appropriately
- [ ] Source panel is visible
- [ ] Message history is accessible

### 6. Document Upload/View

#### Mobile
- [ ] Upload button is accessible
- [ ] File picker works on mobile
- [ ] Document preview is readable
- [ ] Download button works
- [ ] Progress indicator is visible

#### Tablet
- [ ] Document preview is appropriately sized
- [ ] Upload area is touch-friendly

#### Desktop
- [ ] Drag-and-drop works
- [ ] Document preview is large
- [ ] Multiple file upload works

### 7. Forms

#### Mobile
- [ ] Form fields are large enough for touch
- [ ] Input fields don't zoom on focus
- [ ] Select dropdowns work
- [ ] Date pickers work
- [ ] Validation messages are visible
- [ ] Submit button is accessible
- [ ] Form doesn't scroll horizontally

#### Tablet
- [ ] Form layout is appropriate
- [ ] Keyboard doesn't cover inputs

#### Desktop
- [ ] Form fields are appropriately sized
- [ ] Tab order is logical
- [ ] Keyboard shortcuts work

### 8. Admin Dashboard

#### Mobile
- [ ] Admin menu is accessible
- [ ] User list is scrollable
- [ ] Action buttons are touch-friendly
- [ ] Charts are readable

#### Tablet
- [ ] Admin panels display appropriately
- [ ] Data tables are readable

#### Desktop
- [ ] Full admin layout is utilized
- [ ] Data tables are fully visible
- [ ] Advanced controls are accessible

## Performance Testing

### Mobile Performance
- [ ] Initial load time < 3 seconds on 3G
- [ ] Time to interactive < 5 seconds on 3G
- [ ] No layout shifts (CLS < 0.1)
- [ ] First contentful paint < 1.5 seconds

### Desktop Performance
- [ ] Initial load time < 2 seconds on broadband
- [ ] Time to interactive < 3 seconds on broadband
- [ ] Smooth animations (60fps)

## Accessibility Testing

### Keyboard Navigation
- [ ] All interactive elements are keyboard accessible
- [ ] Tab order is logical
- [ ] Focus indicators are visible
- [ ] Escape key closes modals/menus
- [ ] Enter/Space activates buttons

### Screen Reader Compatibility
- [ ] All images have alt text
- [ ] Form labels are associated with inputs
- [ ] ARIA labels are used where appropriate
- [ ] Semantic HTML is used
- [ ] Color contrast meets WCAG AA standards (4.5:1)

### Touch Accessibility
- [ ] Touch targets are at least 44x44px
- [ ] No hover-only interactions
- [ ] Gestures are documented
- [ ] No accidental touches trigger actions

## Common Issues to Check

### Horizontal Scrolling
- Check for elements causing horizontal scroll on mobile
- Verify max-width is set on containers
- Check for overflow: hidden where appropriate

### Text Readability
- Font size is at least 16px on mobile
- Line height is 1.5 or greater
- Text contrast is sufficient
- Text doesn't overflow containers

### Button Sizes
- Primary buttons are at least 44px height on mobile
- Buttons have adequate padding
- Buttons are not too close together

### Images
- Images are responsive (max-width: 100%)
- Images have appropriate alt text
- Images don't cause layout shifts
- Images load progressively

### Modals/Overlays
- Modals fit within viewport on mobile
- Modals can be closed with Escape key
- Modals have close buttons
- Modal overlay covers entire screen

## Testing Procedure

### Manual Testing Steps

1. **Start with Mobile Testing**
   - Open DevTools Device Mode
   - Test with iPhone SE (375px)
   - Go through each page in the checklist
   - Document any issues

2. **Tablet Testing**
   - Switch to iPad (768px)
   - Test all critical user flows
   - Document any issues

3. **Desktop Testing**
   - Switch to desktop view (1920px)
   - Test all features
   - Test keyboard navigation
   - Document any issues

4. **Orientation Testing**
   - Test portrait and landscape on mobile
   - Test portrait and landscape on tablet
   - Ensure layouts adapt correctly

5. **Cross-Browser Testing**
   - Test in Chrome
   - Test in Firefox
   - Test in Safari (if on Mac)
   - Test in Edge

### Automated Testing

Consider using automated tools:
- **Lighthouse**: Run Lighthouse audits for performance and accessibility
- **BrowserStack**: Test on real devices
- **Responsively App**: View multiple screen sizes simultaneously

## Reporting Issues

When reporting responsive design issues, include:
1. Device/screen size where issue occurs
2. Browser and version
3. Screenshot of the issue
4. Steps to reproduce
5. Expected behavior
6. Actual behavior

## Success Criteria

The application is considered responsive when:
- All critical user flows work on mobile (320px+)
- No horizontal scrolling on mobile devices
- All text is readable without zooming
- All interactive elements are accessible via touch
- Layout adapts smoothly between breakpoints
- Performance meets targets on mobile devices
- Accessibility standards are met

## Deferred Testing

The following testing is deferred until after Sprint 8 when infrastructure is deployed:
- Real device testing on physical mobile devices
- Performance testing on real mobile networks
- Cross-browser testing on Safari (iOS)
- Touch gesture testing on real touchscreens
- Accessibility testing with screen readers (JAWS, NVDA)

## References

- [TailwindCSS Responsive Design](https://tailwindcss.com/docs/responsive-design)
- [MDN Responsive Design](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)
- [Web Content Accessibility Guidelines (WCAG)](https://www.w3.org/WAI/WCAG21/quickref/)
- [Google Web Fundamentals - Responsive Design](https://developers.google.com/web/fundamentals/design-and-ux/responsive/)

# T044-T045: Accessibility compliance tests
import pytest
from styles.theme import load_theme, validate_color_contrast, generate_theme_css
from styles.components import style_primary_button, style_text_input


@pytest.mark.ui
@pytest.mark.accessibility
class TestAccessibility:
    """Tests for WCAG 2.1 AA accessibility compliance."""

    def test_color_contrast_wcag_compliance(self, sample_theme):
        """T044: Test all color combinations meet WCAG 2.1 AA standards"""
        palette = sample_theme["color_palette"]
        errors = validate_color_contrast(palette)

        # Should have no contrast errors
        assert len(errors) == 0, f"Color contrast violations: {errors}"

    def test_color_contrast_specific_combinations(self, sample_theme):
        """T045: Test specific critical color combinations"""
        palette = sample_theme["color_palette"]

        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def get_luminance(rgb):
            def normalize(c):
                c = c / 255.0
                return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4)

            r, g, b = [normalize(c) for c in rgb]
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        def contrast_ratio(color1, color2):
            lum1 = get_luminance(hex_to_rgb(color1))
            lum2 = get_luminance(hex_to_rgb(color2))
            lighter = max(lum1, lum2)
            darker = min(lum1, lum2)
            return (lighter + 0.05) / (darker + 0.05)

        # Test critical combinations
        primary_text = palette["primary_colors"]["text_primary"]
        primary_bg = palette["primary_colors"]["background_primary"]
        secondary_text = palette["primary_colors"]["text_secondary"]
        secondary_bg = palette["primary_colors"]["background_secondary"]

        # Primary text on primary background
        ratio1 = contrast_ratio(primary_text, primary_bg)
        assert ratio1 >= 4.5, f"Primary text/background contrast too low: {ratio1:.2f}:1"

        # Secondary text on secondary background
        ratio2 = contrast_ratio(secondary_text, secondary_bg)
        assert ratio2 >= 4.5, f"Secondary text/background contrast too low: {ratio2:.2f}:1"

        # Accent primary on primary background
        accent_primary = palette["accent_colors"]["accent_primary"]
        ratio3 = contrast_ratio(accent_primary, primary_bg)
        assert ratio3 >= 3.0, f"Accent color contrast too low: {ratio3:.2f}:1"

    def test_focus_indicators_present(self, sample_theme):
        """T045: Test that all interactive elements have focus indicators"""
        class MockUITheme:
            def __init__(self, theme_data):
                self.color_palette = theme_data["color_palette"]
                self.typography = theme_data["typography"]
                self.spacing = theme_data["spacing"]

        theme = MockUITheme(sample_theme)

        # Test button focus indicators
        button_css = style_primary_button(theme)
        assert ":focus" in button_css, "Primary button missing focus state"
        assert ("outline:" in button_css or "box-shadow:" in button_css), "Button missing focus indicator"

        # Test input focus indicators
        input_css = style_text_input(theme)
        assert ":focus" in input_css, "Text input missing focus state"
        assert ("outline:" in input_css or "box-shadow:" in input_css), "Input missing focus indicator"

    def test_keyboard_navigation_support(self, sample_theme):
        """T045: Test that keyboard navigation is supported"""
        class MockUITheme:
            def __init__(self, theme_data):
                self.color_palette = theme_data["color_palette"]

        theme = MockUITheme(sample_theme)

        # Check that interactive elements don't disable outline completely
        button_css = style_primary_button(theme)
        input_css = style_text_input(theme)

        # Should not contain "outline: none" without replacement
        if "outline: none" in button_css:
            assert "box-shadow:" in button_css, "Button disables outline without alternative"

        if "outline: none" in input_css:
            assert "box-shadow:" in input_css, "Input disables outline without alternative"

    def test_semantic_color_usage(self, sample_theme):
        """T045: Test that colors are used semantically with text alternatives"""
        palette = sample_theme["color_palette"]

        # Check that semantic colors exist
        accent_colors = palette["accent_colors"]
        assert "accent_success" in accent_colors, "Missing success color"
        assert "accent_warning" in accent_colors, "Missing warning color"
        assert "accent_error" in accent_colors, "Missing error color"

        # Colors should be sufficiently different
        success_color = accent_colors["accent_success"]
        warning_color = accent_colors["accent_warning"]
        error_color = accent_colors["accent_error"]

        assert success_color != warning_color, "Success and warning colors are identical"
        assert success_color != error_color, "Success and error colors are identical"
        assert warning_color != error_color, "Warning and error colors are identical"

    def test_typography_accessibility(self, sample_theme):
        """T045: Test typography choices support accessibility"""
        typography = sample_theme["typography"]

        # Check font family includes fallbacks
        font_family = typography["font_family"]
        assert "sans-serif" in font_family.lower(), "Font family missing sans-serif fallback"

        # Check minimum text sizes
        text_scale = typography["text_scale"]
        base_size = float(text_scale["base"].replace("rem", ""))
        sm_size = float(text_scale["sm"].replace("rem", ""))

        # Base text should be at least 1rem (16px)
        assert base_size >= 1.0, f"Base text size too small: {base_size}rem"

        # Small text should be at least 0.875rem (14px)
        assert sm_size >= 0.875, f"Small text size too small: {sm_size}rem"

        # Check line heights for readability
        line_heights = typography["line_heights"]
        normal_height = line_heights["normal"]
        assert normal_height >= 1.4, f"Normal line height too tight: {normal_height}"

    def test_responsive_text_scaling(self, sample_theme):
        """T045: Test that text scales properly for zoom"""
        from styles.components import generate_responsive_styles

        class MockUITheme:
            def __init__(self, theme_data):
                self.color_palette = theme_data["color_palette"]

        theme = MockUITheme(sample_theme)
        responsive_css = generate_responsive_styles(theme)

        # Should contain media queries for different screen sizes
        assert "@media" in responsive_css, "Missing responsive media queries"
        assert "max-width" in responsive_css, "Missing mobile breakpoints"

        # Should not use fixed pixel units for text in mobile view
        mobile_section = responsive_css.split("@media (max-width: 639px)")[1].split("@media")[0]
        # Mobile text sizing should use relative units
        if "font-size:" in mobile_section:
            assert "rem" in mobile_section or "em" in mobile_section, "Mobile text uses fixed units"

    def test_reduced_motion_support(self, sample_theme):
        """T045: Test that animations respect reduced motion preferences"""
        from styles.components import generate_transition_styles

        animation_css = generate_transition_styles()

        # Should contain reduced motion media query
        assert "@media (prefers-reduced-motion: reduce)" in animation_css, "Missing reduced motion support"

        # Reduced motion section should disable animations
        reduced_motion_section = animation_css.split("@media (prefers-reduced-motion: reduce)")[1]
        assert "animation-duration: 0.01ms" in reduced_motion_section or "transition-duration: 0.01ms" in reduced_motion_section, "Reduced motion not properly implemented"

    def test_theme_css_accessibility_features(self, sample_theme):
        """T045: Test that generated theme CSS includes accessibility features"""
        css = generate_theme_css(sample_theme)

        # Should set proper font family
        assert "font-family:" in css, "Missing font family declaration"

        # Should use relative units for spacing
        assert "rem" in css or "em" in css, "Missing relative units for accessibility"

        # Should include high contrast color definitions
        assert "--color-text-primary:" in css, "Missing primary text color"
        assert "--color-background-primary:" in css, "Missing primary background color"
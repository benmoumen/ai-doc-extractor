"""
T047: Confidence visualization UI component
Visual display of confidence scores and quality metrics
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional


class ConfidenceDisplayUI:
    """UI component for confidence score visualization."""

    CONFIDENCE_COLORS = {
        'very_high': '#22c55e',  # Green
        'high': '#84cc16',       # Light green
        'medium': '#eab308',     # Yellow
        'low': '#f97316',        # Orange
        'very_low': '#ef4444'    # Red
    }

    def render_confidence_overview(self, confidence_data: Dict[str, Any]):
        """Render confidence overview with key metrics"""
        st.subheader("📊 Confidence Analysis")

        overall_confidence = confidence_data.get('overall_confidence', 0)
        confidence_level = confidence_data.get('confidence_level', 'unknown')

        # Overall confidence display
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Large confidence gauge
            self._render_confidence_gauge(overall_confidence, confidence_level)

        with col2:
            st.metric("Confidence Level", confidence_level.replace('_', ' ').title())

        with col3:
            needs_review = confidence_data.get('needs_review', False)
            review_status = "⚠️ Review Needed" if needs_review else "✅ Ready"
            st.metric("Status", review_status)

        # Component scores
        component_scores = confidence_data.get('component_scores', {})
        if component_scores:
            st.write("**Component Analysis:**")
            self._render_component_scores(component_scores)

        # Recommendations
        recommendations = confidence_data.get('recommendations', [])
        if recommendations:
            with st.expander("💡 Recommendations"):
                for rec in recommendations:
                    st.write(f"• {rec}")

    def _render_confidence_gauge(self, confidence: float, level: str):
        """Render confidence gauge chart"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=confidence * 100,
            title={'text': "Overall Confidence"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': self.CONFIDENCE_COLORS.get(level, '#6b7280')},
                'steps': [
                    {'range': [0, 40], 'color': '#fecaca'},
                    {'range': [40, 60], 'color': '#fed7aa'},
                    {'range': [60, 80], 'color': '#fef3c7'},
                    {'range': [80, 90], 'color': '#d9f99d'},
                    {'range': [90, 100], 'color': '#bbf7d0'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    def _render_component_scores(self, component_scores: Dict[str, float]):
        """Render component confidence scores"""
        # Create horizontal bar chart
        components = list(component_scores.keys())
        scores = [component_scores[comp] * 100 for comp in components]
        colors = [self._get_confidence_color(score/100) for score in scores]

        fig = go.Figure(go.Bar(
            x=scores,
            y=[comp.replace('_', ' ').title() for comp in components],
            orientation='h',
            marker_color=colors,
            text=[f'{score:.1f}%' for score in scores],
            textposition='inside'
        ))

        fig.update_layout(
            title="Component Confidence Scores",
            xaxis_title="Confidence %",
            yaxis_title="Components",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_field_confidence_matrix(self, fields_data: List[Dict[str, Any]]):
        """Render field confidence matrix visualization"""
        if not fields_data:
            st.info("No field data available for confidence analysis.")
            return

        st.subheader("🔍 Field Confidence Analysis")

        # Prepare data for heatmap
        field_names = [field.get('display_name', field.get('detected_name', 'Unknown')) for field in fields_data]
        confidence_types = ['visual_clarity_score', 'label_confidence_score', 'value_confidence_score',
                          'type_confidence_score', 'context_confidence_score']

        confidence_matrix = []
        for conf_type in confidence_types:
            row = []
            for field in fields_data:
                score = field.get(conf_type, 0)
                row.append(score * 100)  # Convert to percentage
            confidence_matrix.append(row)

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=confidence_matrix,
            x=field_names,
            y=[ct.replace('_', ' ').title().replace(' Score', '') for ct in confidence_types],
            colorscale='RdYlGn',
            zmin=0,
            zmax=100,
            text=[[f'{val:.0f}%' for val in row] for row in confidence_matrix],
            texttemplate='%{text}',
            hovertemplate='Field: %{x}<br>Metric: %{y}<br>Score: %{z:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            title="Field Confidence Heatmap",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_confidence_distribution(self, schema_confidence_data: Dict[str, Any]):
        """Render confidence distribution charts"""
        st.subheader("📈 Confidence Distribution")

        distribution = schema_confidence_data.get('confidence_distribution', {})
        if not distribution:
            st.info("No distribution data available.")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Pie chart of confidence levels
            labels = list(distribution.keys())
            values = list(distribution.values())
            colors = [self.CONFIDENCE_COLORS.get(label, '#6b7280') for label in labels]

            fig = go.Figure(data=[go.Pie(
                labels=[l.replace('_', ' ').title() for l in labels],
                values=values,
                marker_colors=colors,
                hole=0.4
            )])

            fig.update_layout(
                title="Field Confidence Distribution",
                height=300,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Bar chart of confidence stats
            stats = schema_confidence_data.get('field_confidence_stats', {})
            if stats:
                metrics = ['mean', 'median', 'min', 'max']
                values = [stats.get(metric, 0) * 100 for metric in metrics]

                fig = go.Figure(data=[go.Bar(
                    x=[m.title() for m in metrics],
                    y=values,
                    marker_color=['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
                    text=[f'{v:.1f}%' for v in values],
                    textposition='outside'
                )])

                fig.update_layout(
                    title="Confidence Statistics",
                    yaxis_title="Confidence %",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20)
                )

                st.plotly_chart(fig, use_container_width=True)

    def render_confidence_trend(self, historical_data: List[Dict[str, Any]]):
        """Render confidence trend over time"""
        if not historical_data:
            st.info("No historical data available for trend analysis.")
            return

        st.subheader("📈 Confidence Trends")

        # Extract data for trend
        timestamps = [entry.get('timestamp', '') for entry in historical_data]
        confidences = [entry.get('confidence', 0) * 100 for entry in historical_data]

        fig = go.Figure()

        # Add confidence trend line
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=confidences,
            mode='lines+markers',
            name='Confidence',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8)
        ))

        # Add confidence threshold lines
        fig.add_hline(y=80, line_dash="dash", line_color="green",
                     annotation_text="High Confidence Threshold")
        fig.add_hline(y=60, line_dash="dash", line_color="orange",
                     annotation_text="Medium Confidence Threshold")

        fig.update_layout(
            title="Confidence Over Time",
            xaxis_title="Analysis Date",
            yaxis_title="Confidence %",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_model_comparison(self, comparison_data: Dict[str, Any]):
        """Render model performance comparison"""
        if not comparison_data:
            st.info("No comparison data available.")
            return

        st.subheader("🤖 Model Performance Comparison")

        model_performance = comparison_data.get('model_performance', {})
        if not model_performance:
            return

        models = list(model_performance.keys())
        avg_confidences = [model_performance[model].get('average_confidence', 0) * 100
                          for model in models]
        best_confidences = [model_performance[model].get('best_confidence', 0) * 100
                          for model in models]
        counts = [model_performance[model].get('count', 0) for model in models]

        fig = go.Figure()

        # Average confidence bars
        fig.add_trace(go.Bar(
            name='Average Confidence',
            x=models,
            y=avg_confidences,
            marker_color='#3b82f6',
            text=[f'{c:.1f}%' for c in avg_confidences],
            textposition='outside'
        ))

        # Best confidence line
        fig.add_trace(go.Scatter(
            name='Best Confidence',
            x=models,
            y=best_confidences,
            mode='lines+markers',
            line=dict(color='#10b981', width=3),
            marker=dict(size=10, symbol='diamond')
        ))

        fig.update_layout(
            title="Model Performance Comparison",
            xaxis_title="AI Models",
            yaxis_title="Confidence %",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Model usage statistics
        col1, col2, col3 = st.columns(3)
        for i, (model, stats) in enumerate(model_performance.items()):
            col = [col1, col2, col3][i % 3]
            with col:
                st.metric(
                    model.replace('/', ' ').title(),
                    f"{stats.get('average_confidence', 0):.1%}",
                    f"{stats.get('count', 0)} analyses"
                )

    def _get_confidence_color(self, confidence: float) -> str:
        """Get color based on confidence level"""
        if confidence >= 0.9:
            return self.CONFIDENCE_COLORS['very_high']
        elif confidence >= 0.8:
            return self.CONFIDENCE_COLORS['high']
        elif confidence >= 0.6:
            return self.CONFIDENCE_COLORS['medium']
        elif confidence >= 0.4:
            return self.CONFIDENCE_COLORS['low']
        else:
            return self.CONFIDENCE_COLORS['very_low']

    def render_confidence_insights(self, confidence_data: Dict[str, Any]):
        """Render confidence insights and recommendations"""
        st.subheader("🔍 Confidence Insights")

        overall_confidence = confidence_data.get('overall_confidence', 0)
        component_scores = confidence_data.get('component_scores', {})

        # Key insights
        insights = []

        if overall_confidence >= 0.9:
            insights.append("🟢 Excellent overall confidence - schema is production-ready")
        elif overall_confidence >= 0.8:
            insights.append("🟢 High confidence - minimal review needed")
        elif overall_confidence >= 0.6:
            insights.append("🟡 Medium confidence - review recommended")
        else:
            insights.append("🔴 Low confidence - thorough review required")

        # Component-specific insights
        if component_scores:
            lowest_component = min(component_scores.items(), key=lambda x: x[1])
            highest_component = max(component_scores.items(), key=lambda x: x[1])

            if lowest_component[1] < 0.5:
                insights.append(f"⚠️ {lowest_component[0].replace('_', ' ').title()} has low confidence ({lowest_component[1]:.1%})")

            if highest_component[1] > 0.8:
                insights.append(f"✅ {highest_component[0].replace('_', ' ').title()} has high confidence ({highest_component[1]:.1%})")

        # Display insights
        for insight in insights:
            st.write(f"• {insight}")

        # Actionable recommendations
        self._render_actionable_recommendations(confidence_data)

    def _render_actionable_recommendations(self, confidence_data: Dict[str, Any]):
        """Render actionable recommendations based on confidence analysis"""
        st.write("**Recommended Actions:**")

        actions = []
        overall_confidence = confidence_data.get('overall_confidence', 0)
        component_scores = confidence_data.get('component_scores', {})

        if overall_confidence < 0.6:
            actions.append("🔄 Consider re-analyzing with a different AI model")
            actions.append("📝 Review and manually adjust low-confidence fields")

        if component_scores.get('field_extraction', 0) < 0.6:
            actions.append("📄 Check document quality - ensure good resolution and clarity")

        if component_scores.get('document_type', 0) < 0.7:
            actions.append("🏷️ Manually verify document type classification")

        if component_scores.get('validation_rules', 0) < 0.5:
            actions.append("✅ Add custom validation rules for important fields")

        if not actions:
            actions.append("✅ Confidence levels are good - proceed with schema usage")

        for action in actions:
            st.write(f"• {action}")

    def get_confidence_summary(self, confidence_data: Dict[str, Any]) -> str:
        """Get text summary of confidence analysis"""
        overall_confidence = confidence_data.get('overall_confidence', 0)
        confidence_level = confidence_data.get('confidence_level', 'unknown')
        field_count = confidence_data.get('field_count', 0)
        high_conf_fields = confidence_data.get('high_confidence_fields', 0)

        summary = f"Analysis shows {confidence_level.replace('_', ' ')} confidence ({overall_confidence:.1%}) "
        summary += f"with {high_conf_fields} of {field_count} fields having high confidence. "

        if confidence_data.get('needs_review', False):
            summary += "Manual review is recommended before production use."
        else:
            summary += "Schema appears ready for production use."

        return summary
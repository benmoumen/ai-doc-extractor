"""
T044: Document upload UI component
Specialized component for document upload with validation and preview
"""

import streamlit as st
import io
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image
import base64

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from ..services.document_processor import DocumentProcessor


class DocumentUploadUI:
    """UI component for document upload with validation and preview."""

    SUPPORTED_FORMATS = {
        'Images': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'],
        'Documents': ['pdf']
    }

    MAX_FILE_SIZE_MB = 50
    MAX_PREVIEW_SIZE = (800, 600)

    def __init__(self):
        """Initialize upload UI component"""
        self.processor = DocumentProcessor()

    def render_upload_interface(self) -> Optional[Dict[str, Any]]:
        """
        Render document upload interface

        Returns:
            Dictionary with upload results or None if no file uploaded
        """
        st.subheader("📤 Document Upload")

        # Upload instructions
        self._show_upload_instructions()

        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a document file",
            type=list(self.SUPPORTED_FORMATS['Images']) + list(self.SUPPORTED_FORMATS['Documents']),
            help=f"Maximum file size: {self.MAX_FILE_SIZE_MB}MB"
        )

        if uploaded_file is not None:
            # Validate file
            validation_result = self._validate_uploaded_file(uploaded_file)

            if validation_result['valid']:
                # Show file information
                self._show_file_info(uploaded_file, validation_result)

                # Show preview
                preview_success = self._show_file_preview(uploaded_file)

                # Upload options
                upload_options = self._render_upload_options()

                # Process upload button
                if st.button("✅ Process Upload", type="primary"):
                    return self._process_upload(uploaded_file, upload_options, validation_result)

            else:
                st.error(f"❌ File validation failed: {validation_result['error']}")

        return None

    def _show_upload_instructions(self):
        """Show upload instructions and requirements"""
        with st.expander("📋 Upload Instructions", expanded=False):
            st.write("**Supported File Types:**")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Images:**")
                for fmt in self.SUPPORTED_FORMATS['Images']:
                    st.write(f"• {fmt.upper()}")

            with col2:
                st.write("**Documents:**")
                for fmt in self.SUPPORTED_FORMATS['Documents']:
                    st.write(f"• {fmt.upper()}")

            st.write("**Requirements:**")
            st.write(f"• Maximum file size: {self.MAX_FILE_SIZE_MB}MB")
            st.write("• Clear text and good image quality")
            st.write("• Preferably high resolution (>300 DPI)")
            st.write("• Minimal skew or rotation")

            st.write("**Best Practices:**")
            st.write("• Scan documents at 300+ DPI")
            st.write("• Ensure good lighting for photos")
            st.write("• Crop to remove unnecessary borders")
            st.write("• Use portrait orientation for better processing")

    def _validate_uploaded_file(self, uploaded_file) -> Dict[str, Any]:
        """Validate uploaded file"""
        try:
            # Check file size
            file_size = len(uploaded_file.getvalue())

            if file_size > self.MAX_FILE_SIZE_MB * 1024 * 1024:
                return {
                    'valid': False,
                    'error': f"File too large: {file_size / (1024 * 1024):.1f}MB (max: {self.MAX_FILE_SIZE_MB}MB)"
                }

            # Check file format
            file_extension = uploaded_file.name.lower().split('.')[-1]
            all_supported = self.SUPPORTED_FORMATS['Images'] + self.SUPPORTED_FORMATS['Documents']

            if file_extension not in all_supported:
                return {
                    'valid': False,
                    'error': f"Unsupported file format: {file_extension}"
                }

            # Determine file type
            if file_extension in self.SUPPORTED_FORMATS['Images']:
                file_type = 'image'
                # Validate image
                try:
                    with Image.open(io.BytesIO(uploaded_file.getvalue())) as img:
                        width, height = img.size
                        format_info = img.format
                        mode = img.mode
                except Exception as e:
                    return {
                        'valid': False,
                        'error': f"Invalid image file: {str(e)}"
                    }

                validation_info = {
                    'dimensions': (width, height),
                    'format': format_info,
                    'mode': mode,
                    'is_large': width > 2000 or height > 2000
                }

            elif file_extension == 'pdf':
                file_type = 'pdf'
                # Validate PDF
                if PYMUPDF_AVAILABLE:
                    try:
                        doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
                        page_count = doc.page_count
                        doc.close()
                    except Exception as e:
                        return {
                            'valid': False,
                            'error': f"Invalid PDF file: {str(e)}"
                        }

                    validation_info = {
                        'page_count': page_count,
                        'multi_page': page_count > 1
                    }
                else:
                    validation_info = {
                        'page_count': 1,  # Assume single page
                        'multi_page': False,
                        'pymupdf_unavailable': True
                    }

            return {
                'valid': True,
                'file_type': file_type,
                'file_size': file_size,
                'file_extension': file_extension,
                'validation_info': validation_info
            }

        except Exception as e:
            return {
                'valid': False,
                'error': f"Validation error: {str(e)}"
            }

    def _show_file_info(self, uploaded_file, validation_result: Dict[str, Any]):
        """Show file information"""
        st.write("**📄 File Information:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Name:** {uploaded_file.name}")
            st.write(f"**Type:** {validation_result['file_type'].upper()}")

        with col2:
            file_size_mb = validation_result['file_size'] / (1024 * 1024)
            st.write(f"**Size:** {file_size_mb:.2f} MB")
            st.write(f"**Format:** {validation_result['file_extension'].upper()}")

        with col3:
            validation_info = validation_result['validation_info']

            if validation_result['file_type'] == 'image':
                width, height = validation_info['dimensions']
                st.write(f"**Dimensions:** {width} × {height}")
                st.write(f"**Color Mode:** {validation_info['mode']}")

                # Quality assessment
                if validation_info['is_large']:
                    st.success("🟢 High resolution")
                else:
                    st.warning("🟡 Medium resolution")

            elif validation_result['file_type'] == 'pdf':
                st.write(f"**Pages:** {validation_info['page_count']}")

                if validation_info['multi_page']:
                    st.info("📄 Multi-page document")
                else:
                    st.success("📄 Single page")

    def _show_file_preview(self, uploaded_file) -> bool:
        """Show file preview"""
        try:
            st.write("**👁️ Document Preview:**")

            file_extension = uploaded_file.name.lower().split('.')[-1]

            if file_extension in self.SUPPORTED_FORMATS['Images']:
                # Image preview
                image = Image.open(io.BytesIO(uploaded_file.getvalue()))

                # Resize for preview if needed
                if image.size[0] > self.MAX_PREVIEW_SIZE[0] or image.size[1] > self.MAX_PREVIEW_SIZE[1]:
                    image.thumbnail(self.MAX_PREVIEW_SIZE, Image.Resampling.LANCZOS)

                st.image(image, caption=f"Preview: {uploaded_file.name}", use_column_width=True)

                # Image quality assessment
                self._assess_image_quality(image)

                return True

            elif file_extension == 'pdf' and PYMUPDF_AVAILABLE:
                # PDF preview (first page)
                try:
                    doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")

                    if doc.page_count > 0:
                        # Convert first page to image
                        page = doc[0]
                        mat = fitz.Matrix(1.5, 1.5)  # 1.5x zoom
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")

                        # Display preview
                        st.image(
                            img_data,
                            caption=f"PDF Preview: Page 1 of {doc.page_count}",
                            use_column_width=True
                        )

                        if doc.page_count > 1:
                            st.info(f"📄 This PDF has {doc.page_count} pages. Only the first page is shown in preview.")

                    doc.close()
                    return True

                except Exception as e:
                    st.warning(f"Could not generate PDF preview: {str(e)}")
                    return False

            else:
                st.info("Preview not available for this file type.")
                return False

        except Exception as e:
            st.error(f"Preview error: {str(e)}")
            return False

    def _assess_image_quality(self, image: Image.Image):
        """Assess and display image quality information"""
        width, height = image.size
        total_pixels = width * height

        quality_indicators = []

        # Resolution assessment
        if total_pixels >= 2000000:  # 2MP+
            quality_indicators.append("🟢 High resolution")
        elif total_pixels >= 500000:  # 0.5MP+
            quality_indicators.append("🟡 Medium resolution")
        else:
            quality_indicators.append("🔴 Low resolution")

        # Aspect ratio assessment
        aspect_ratio = width / height
        if 0.7 <= aspect_ratio <= 1.4:
            quality_indicators.append("🟢 Good aspect ratio")
        else:
            quality_indicators.append("🟡 Unusual aspect ratio")

        # Color mode assessment
        if image.mode == 'RGB':
            quality_indicators.append("🟢 Full color")
        elif image.mode == 'L':
            quality_indicators.append("🟡 Grayscale")
        else:
            quality_indicators.append("🟡 Other color mode")

        # Display quality assessment
        with st.expander("📊 Image Quality Assessment"):
            for indicator in quality_indicators:
                st.write(f"• {indicator}")

            st.write(f"**Technical Details:**")
            st.write(f"• Resolution: {width} × {height} ({total_pixels:,} pixels)")
            st.write(f"• Aspect Ratio: {aspect_ratio:.2f}")
            st.write(f"• Color Mode: {image.mode}")
            st.write(f"• Format: {image.format}")

    def _render_upload_options(self) -> Dict[str, Any]:
        """Render upload options and settings"""
        st.write("**⚙️ Processing Options:**")

        col1, col2 = st.columns(2)

        with col1:
            document_type_hint = st.selectbox(
                "Document Type Hint",
                options=[
                    "Auto-detect",
                    "Invoice",
                    "Receipt",
                    "Form",
                    "Driver's License",
                    "Passport",
                    "Bank Statement",
                    "Tax Document",
                    "Contract",
                    "Insurance Policy",
                    "Certificate"
                ],
                help="Hint to improve document type detection"
            )

        with col2:
            quality_mode = st.selectbox(
                "Processing Quality",
                options=["Standard", "High Quality", "Fast"],
                help="Processing quality vs speed tradeoff"
            )

        # Advanced options
        with st.expander("🔧 Advanced Options"):
            col1, col2 = st.columns(2)

            with col1:
                auto_rotate = st.checkbox(
                    "Auto-rotate document",
                    value=True,
                    help="Automatically detect and correct document orientation"
                )

                enhance_contrast = st.checkbox(
                    "Enhance contrast",
                    value=False,
                    help="Improve contrast for better text recognition"
                )

            with col2:
                remove_background = st.checkbox(
                    "Remove background",
                    value=False,
                    help="Remove background noise for cleaner analysis"
                )

                preserve_colors = st.checkbox(
                    "Preserve original colors",
                    value=True,
                    help="Keep original colors vs convert to grayscale"
                )

        return {
            'document_type_hint': None if document_type_hint == "Auto-detect" else document_type_hint.lower().replace(" ", "_"),
            'quality_mode': quality_mode.lower().replace(" ", "_"),
            'auto_rotate': auto_rotate,
            'enhance_contrast': enhance_contrast,
            'remove_background': remove_background,
            'preserve_colors': preserve_colors
        }

    def _process_upload(self, uploaded_file, options: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process the uploaded file"""
        try:
            with st.spinner("📄 Processing uploaded document..."):
                # Read file content
                file_content = uploaded_file.getvalue()

                # Create metadata with processing options
                metadata = {
                    'upload_timestamp': st.session_state.get('upload_timestamp', ''),
                    'original_size': len(file_content),
                    'validation_info': validation_result['validation_info'],
                    'processing_options': options,
                    'ui_component': 'document_upload_ui'
                }

                # Process upload using DocumentProcessor
                document = self.processor.process_upload(
                    file_content=file_content,
                    filename=uploaded_file.name,
                    metadata=metadata
                )

                st.success("✅ Document uploaded and processed successfully!")

                # Show processing results
                self._show_processing_results(document, validation_result)

                return {
                    'success': True,
                    'document': document,
                    'processing_options': options,
                    'validation_result': validation_result
                }

        except Exception as e:
            st.error(f"❌ Upload processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_options': options,
                'validation_result': validation_result
            }

    def _show_processing_results(self, document, validation_result: Dict[str, Any]):
        """Show document processing results"""
        st.write("**✅ Processing Complete:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Document ID:** {document.id[:8]}...")
            st.write(f"**Status:** {document.processing_status.title()}")

        with col2:
            st.write(f"**File Type:** {document.file_type.upper()}")
            st.write(f"**File Size:** {document.file_size / 1024:.1f} KB")

        with col3:
            st.write(f"**Content Hash:** {document.content_hash[:8]}...")
            st.write(f"**Processed:** {document.upload_timestamp.strftime('%H:%M:%S')}")

        # Processing statistics
        if document.metadata:
            with st.expander("📊 Processing Details"):
                st.json(document.metadata)

    def render_bulk_upload_interface(self) -> Optional[List[Dict[str, Any]]]:
        """
        Render bulk upload interface for multiple documents

        Returns:
            List of upload results or None
        """
        st.subheader("📤 Bulk Document Upload")

        st.info("Upload multiple documents for batch processing")

        # Bulk file uploader
        uploaded_files = st.file_uploader(
            "Choose document files",
            type=list(self.SUPPORTED_FORMATS['Images']) + list(self.SUPPORTED_FORMATS['Documents']),
            accept_multiple_files=True,
            help=f"Maximum {self.MAX_FILE_SIZE_MB}MB per file"
        )

        if uploaded_files:
            st.write(f"**Selected {len(uploaded_files)} files:**")

            # Show file list
            valid_files = []
            invalid_files = []

            for file in uploaded_files:
                validation = self._validate_uploaded_file(file)
                if validation['valid']:
                    valid_files.append((file, validation))
                    st.success(f"✅ {file.name} - Valid")
                else:
                    invalid_files.append((file, validation))
                    st.error(f"❌ {file.name} - {validation['error']}")

            if invalid_files:
                st.warning(f"⚠️ {len(invalid_files)} files failed validation and will be skipped.")

            if valid_files:
                # Bulk processing options
                options = self._render_upload_options()

                # Process all button
                if st.button(f"🚀 Process All {len(valid_files)} Files", type="primary"):
                    return self._process_bulk_upload(valid_files, options)

        return None

    def _process_bulk_upload(self, valid_files: List[Tuple], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process multiple files in bulk"""
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, (file, validation) in enumerate(valid_files):
            try:
                status_text.text(f"Processing {file.name} ({i+1}/{len(valid_files)})...")
                progress_bar.progress((i + 1) / len(valid_files))

                # Process single file
                result = self._process_upload(file, options, validation)
                results.append(result)

                if result['success']:
                    st.success(f"✅ {file.name} processed successfully")
                else:
                    st.error(f"❌ {file.name} failed: {result['error']}")

            except Exception as e:
                st.error(f"❌ {file.name} failed: {str(e)}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'filename': file.name
                })

        status_text.text("✅ Bulk processing completed!")

        # Show summary
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful

        st.write(f"**📊 Bulk Processing Summary:**")
        st.write(f"• ✅ Successful: {successful}")
        st.write(f"• ❌ Failed: {failed}")
        st.write(f"• 📄 Total: {len(results)}")

        return results

    def get_upload_statistics(self) -> Dict[str, Any]:
        """Get upload component statistics"""
        return {
            'supported_formats': self.SUPPORTED_FORMATS,
            'max_file_size_mb': self.MAX_FILE_SIZE_MB,
            'preview_max_size': self.MAX_PREVIEW_SIZE,
            'pymupdf_available': PYMUPDF_AVAILABLE,
            'processor_available': True
        }
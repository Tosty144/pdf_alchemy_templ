import pymupdf  # PyMuPDF
import os
from deep_translator import GoogleTranslator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

class Cmdline:
    def __init__(self, args) -> None:
        self.args = args
        self.input_pdf = ""
        self.output_pdf = ""

    def get_num_pages(self):
        """Print the total number of pages in the input PDF."""
        doc = pymupdf.open(self.args.file_path)  # open a document
        print(f"Total pages: {doc.page_count}")
        doc.close()

    def split_pdf(self):
        """Split the input PDF into multiple PDFs based on page ranges.
        args.split is a list where each element is a list of zero-based page indices.
        The output_path is treated as a directory; files are named part_1.pdf, part_2.pdf, …
        """
        if not self.args.split:
            print("no split ranges provided.")
            return
        os.makedirs(self.args.output_path, exist_ok=True)
        src = pymupdf.open(self.args.file_path)
        for idx, pages in enumerate(self.args.split, start=1):
            new_doc = pymupdf.open()  # create a new PDF
            for p in pages:
                new_doc.insert_pdf(src, from_page=p, to_page=p)
            out_file = os.path.join(self.args.output_path, f"part_{idx}.pdf")
            new_doc.save(out_file)
            new_doc.close()
        src.close()
        print(f"created {len(self.args.split)} split PDFs in {self.args.output_path}")

    def del_range(self):
        """Delete the specified pages from the input PDF and write the result to output_path.
        args.delete is a list of lists of zero-based page numbers. We flatten it.
        """
        if not self.args.delete:
            print("No pages specified for deletion")
            return
        pages_to_remove = sorted({p for sub in self.args.delete for p in sub})
        print(f"pages_to_remove: {pages_to_remove}")
        out_dir = os.path.dirname(self.args.output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        src = pymupdf.open(self.args.file_path)
        new_doc = pymupdf.Document()
        for i in range(src.page_count):
            if i not in pages_to_remove:
                new_doc.insert_pdf(src, from_page=i, to_page=i)
        new_doc.save(self.args.output_path)
        new_doc.close()
        src.close()
        print(f"Saved PDF without specified pages to {self.args.output_path}")

    def add_pdf(self):
        """Add pages from another PDF into the source PDF.
        The insert PDF is provided via the positional argument `insert`.
        Insertion point is defined by either `--after` or `--before` (1-based).
        The result is written to output_path.
        """
        out_dir = os.path.dirname(self.args.output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        src = pymupdf.open(self.args.file_path)
        insert_doc = pymupdf.open(self.args.insert)

        # Determine the zero-based insertion point.
        # --after N  -> insert right after page N (1-based), i.e. before zero-based index N
        # --before N -> insert right before page N (1-based), i.e. before zero-based index N-1
        if getattr(self.args, "after", None) is not None:
            insert_at = self.args.after  # after page N (1-based) == zero-based index N
        elif getattr(self.args, "before", None) is not None:
            insert_at = self.args.before - 1
        else:
            insert_at = src.page_count  # default: append at the end

        # Clamp to valid range
        insert_at = max(0, min(insert_at, src.page_count))

        src.insert_pdf(insert_doc, start_at=insert_at)
        src.save(self.args.output_path)
        src.close()
        insert_doc.close()
        print(f"Inserted {self.args.insert} into {self.args.file_path} at position {insert_at}, "
              f"saved to {self.args.output_path}")

    def crop_half(self):
        """Crop specified pages in half (left and right) and duplicate each as two pages.
        args.crop_half provides page ranges (zero-based). For each page we create two pages:
        one with the left half of the original media box and one with the right half.
        The result is saved to output_path.
        """
        if not self.args.crop_half:
            print("No pages specified for cropping")
            return
        pages_to_crop = sorted({p for sub in self.args.crop_half for p in sub})
        out_dir = os.path.dirname(self.args.output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        src = pymupdf.open(self.args.file_path)
        new_doc = pymupdf.open()

        for i in range(src.page_count):
            if i in pages_to_crop:
                rect = src[i].rect
                mid_x = (rect.x0 + rect.x1) / 2

                left_rect = pymupdf.Rect(rect.x0, rect.y0, mid_x, rect.y1)
                right_rect = pymupdf.Rect(mid_x, rect.y0, rect.x1, rect.y1)

                for half_rect in (left_rect, right_rect):
                    new_page = new_doc.new_page(width=half_rect.width, height=half_rect.height)
                    new_page.show_pdf_page(new_page.rect, src, i, clip=half_rect)
            else:
                new_doc.insert_pdf(src, from_page=i, to_page=i)

        new_doc.save(self.args.output_path)
        new_doc.close()
        src.close()
        print(f"Saved cropped PDF to {self.args.output_path}")

    def extract_text(self, page_range=None):
        """Extrae el texto del PDF. page_range: lista de índices zero-based, o None para todo."""
        doc = pymupdf.open(self.args.file_path)
        pages = page_range if page_range else range(doc.page_count)
        text_parts = []
        for i in pages:
            text_parts.append(doc[i].get_text())
        doc.close()
        return "\n\n".join(text_parts)

    def _save_text_as_pdf(self, text, output_path, title=None):
        """Crea un PDF nuevo con el texto dado, envolviendo líneas y agregando páginas
        cuando el contenido no cabe en una sola.
        """
        import textwrap

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        doc = pymupdf.open()
        fontsize = 11
        margin = 50
        line_height = fontsize * 1.4
        page_width, page_height = 595, 842  # tamaño A4 en puntos
        usable_width = page_width - 2 * margin
        usable_height = page_height - 2 * margin
        chars_per_line = int(usable_width / (fontsize * 0.5))  # estimado para helvética
        lines_per_page = int(usable_height / line_height)

        # Envolvemos cada párrafo por separado para conservar los saltos de línea originales
        all_lines = []
        if title:
            all_lines.extend([title, ""])
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                all_lines.append("")
                continue
            all_lines.extend(textwrap.wrap(paragraph, width=chars_per_line) or [""])

        # Repartimos las líneas en páginas
        for start in range(0, len(all_lines), lines_per_page):
            page_lines = all_lines[start:start + lines_per_page]
            page = doc.new_page(width=page_width, height=page_height)
            y = margin + fontsize
            for line in page_lines:
                page.insert_text((margin, y), line, fontsize=fontsize, fontname="helv")
                y += line_height

        doc.save(output_path)
        doc.close()

    def summarize_pdf(self):
        """Genera un resumen ejecutivo y los puntos clave del PDF (extractivo, 100% local, sin costo)."""
        text = self.extract_text()

        # idioma para el tokenizador: si no se especifica, usamos español por defecto
        lang = getattr(self.args, "summary_lang", None) or "spanish"

        parser = PlaintextParser.from_string(text, Tokenizer(lang))
        summarizer = TextRankSummarizer()
        sentence_count = 8
        summary_sentences = summarizer(parser.document, sentence_count)

        result_lines = []
        for i, sentence in enumerate(summary_sentences, start=1):
            result_lines.append(f"{i}. {sentence}")
        result = "\n".join(result_lines)

        print(result)

        if self.args.output_path:
            self._save_text_as_pdf(result, self.args.output_path, title="Puntos clave")
            print(f"Resumen guardado en {self.args.output_path}")

    def translate_pdf(self):
        """Traduce el contenido del PDF al idioma indicado (gratis, vía Google Translate)."""
        target_lang = self.args.target_lang
        text = self.extract_text()

        # Google Translate (gratuito) tiene un límite de ~5000 caracteres por solicitud,
        # así que troceamos el texto en bloques seguros.
        chunk_size = 4500
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

        translator = GoogleTranslator(source="auto", target=target_lang)
        translated_parts = []
        for idx, chunk in enumerate(chunks, start=1):
            if not chunk.strip():
                continue
            translated_parts.append(translator.translate(chunk))
            print(f"Traducido bloque {idx}/{len(chunks)}")

        translated = "\n\n".join(translated_parts)

        self._save_text_as_pdf(translated, self.args.output_path)
        print(f"Traducción guardada en {self.args.output_path}")
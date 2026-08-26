import argparse

class PDFArgumentParser():
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Split and list num of pages of a PDF")
        self._configure_parser()
        self._configure_subparsers()

    def _configure_parser(self):
        self.parser.add_argument(
            "-f", "--file",
            dest="file_path",
            type=str,
            help="Get the PDF file location",
            required=True
        )
        self.parser.add_argument(
            "-o", "--output",
            dest="output_path",
            type=str,
            help="Direct the output directory/file",
        )
        self.parser.add_argument(
            "-tp", "--total-pages",
            help="From the file location get total pages of the PDF",
            action="store_true"
        )
        self.parser.add_argument(
            "-s", "--split",
            help="It splits a file to multiple files with a range of pages '--split 1-30 31-40' or single pages '--split 1 4 6' given by the user",
            nargs="+",
            type=self.parse_input
        )
        self.parser.add_argument(
            "-d", "--delete",
            help="It deletes a range of pages '--del 1-5' or a single page '--delete 1 3 5' from a PDF and makes a copy with the deleted pages",
            nargs="+",
            type=self.parse_input
        )
        self.parser.add_argument(
            "-ch", "--crop-half",
            help="From a range of pages it crops by half and gets the left and right side to create 2 new pages and output to copy of the modified file '--crop-half 1-30 31-40' or single pages '--crop 1 4 6' given by the user",
            nargs="+",
            type=self.parse_input
        )


    def _configure_subparsers(self):
        subparsers = self.parser.add_subparsers(dest='command')
        add_parser = subparsers.add_parser("add", help="Add a PDF file into another")
        add_parser.add_argument("insert", help="PDF to insert")

        position_group = add_parser.add_mutually_exclusive_group(required=True)
        position_group.add_argument(
            "--after",
            help="Adds the number of pages AFTER the specified page '--file source.pdf add insert.pdf --after 60'",
            type=int
        )
        position_group.add_argument(
            "--before",
            help="Adds the number of pages BEFORE the specified page '--file source.pdf add insert.pdf --before 60'",
            type=int
        )

        # --- NUEVO: resumen ejecutivo + puntos clave ---
        subparsers.add_parser(
            "summarize",
            help="Genera un resumen ejecutivo y los puntos clave del PDF usando un LLM"
        )

        # --- NUEVO: traducción contextual ---
        translate_parser = subparsers.add_parser(
            "translate",
            help="Traduce el contenido del PDF a otro idioma, conservando el sentido contextual"
        )
        translate_parser.add_argument(
            "--target-lang",
            dest="target_lang",
            required=True,
            help="Idioma destino, ej: en, fr, pt"
        )


    def parse_input(self, value):
       if "-" in value:
            start, end = map(int, value.split("-"))
            if  start > end:
                self.parser.error(f"ERR: Start range {start} is higher than end range {end}")

            if start < 1 or end < 1:
                self.parser.error(f"ERR: start {start} or end {end} range must be positive numbers")
            return list(range(start - 1, end))
       single_page = int(value)
       if single_page < 1:
           self.parser.error(f"ERR: Page {single_page} has to be positive")
       return [int(value) - 1]

    def get_args(self):
        return self.parser.parse_args()
    
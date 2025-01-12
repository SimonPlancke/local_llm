from file_processing import TextFileMethods, PDFFileMethods, FolderMethods, TranscriptionMethods

output_file = 'uncompressed_output.txt'
processed_file = 'xml_parsed_output.txt'
TextFileMethods.parse_text_as_xml(input_file=output_file, output_file=processed_file)

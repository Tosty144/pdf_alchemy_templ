from cmdline import Cmdline
from parseargs import PDFArgumentParser

def main():
    parser = PDFArgumentParser()
    args = parser.get_args()
    app = Cmdline(args)

    print("""
'||'''|, '||'''|. '||''''|                                 
 ||   ||  ||   ||  ||  .                                   
 ||...|'  ||   ||  ||''|                                   
 ||       ||   ||  ||                                      
.||      .||...|' .||.                                     
                                                           
                                                           
     /.      '||`       '||                               
    // \\      ||         ||                               
   //...\\     ||  .|'',  ||''|, .|''|, '||),,(|,  '||  ||`
  //     \\    ||  ||     ||  || ||..||  || || ||   `|..|| 
.//       \\. .||. `|..' .||  || `|...  .||    ||.      || 
    """)
    # Determine which operation to perform based on provided arguments
    if app.args.total_pages:
        app.get_num_pages()
    elif app.args.split:
        app.split_pdf()
    elif app.args.delete:
        app.del_range()
    elif app.args.crop_half:
        app.crop_half()
    elif app.args.command == "add":
        app.add_pdf()
    elif app.args.command == "summarize":
        app.summarize_pdf()
    elif app.args.command == "translate":
        app.translate_pdf()
    else:
        print("No arguments used, try 'uv run main.py -h'")


if __name__ == "__main__":
    main()

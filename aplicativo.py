"""Abre a janela nativa de apresentação do monitoramento de vagas."""
import argparse
from pathlib import Path
import sys


def main():
    root=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usar-resultados',action='store_true',help='Abrir a análise já concluída, sem reprocessar.')
    args=parser.parse_args()
    try:
        from PySide6.QtWidgets import QApplication
        from app.janela import MainWindow,configure_application
        from app.modelo import load_session
    except ImportError:
        parser.exit(1,'Instale as dependências do aplicativo com: python -m pip install -r requirements-app.txt\n')
    session=None
    if args.usar_resultados:
        try:session=load_session(root)
        except (OSError,ValueError,KeyError,TypeError) as error:parser.exit(1,f'Análise indisponível: {error}\nAbra sem --usar-resultados para reprocessar.\n')
    application=QApplication([sys.argv[0]])
    configure_application(application)
    window=MainWindow(root,session=session)
    window.show()
    return application.exec()


if __name__=='__main__':
    raise SystemExit(main())

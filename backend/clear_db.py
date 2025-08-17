#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
load_dotenv()

from api import create_app, db
from api.models import BlogPost
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='Skrypt do czyszczenia bazy danych (drafts lub all).')
    parser.add_argument('--mode', choices=['drafts', 'all'], default='drafts',
                        help="'drafts' - usuń tylko wersje robocze; 'all' - usuń wszystkie posty.")
    parser.add_argument('--yes', action='store_true', help='Automatycznie potwierdź usunięcie bez promptu.')
    return parser.parse_args()


def main():
    args = parse_args()

    app = create_app()
    with app.app_context():
        if args.mode == 'drafts':
            query = BlogPost.query.filter_by(status='draft')
        else:
            query = BlogPost.query

        total = query.count()
        print(f"Znaleziono {total} posta(ów) do usunięcia (tryb={args.mode}).")

        if total == 0:
            print('Brak rekordów do usunięcia. Kończę.')
            return

        if not args.yes:
            confirm = input('Aby potwierdzić usunięcie wpisz EXACT "YES": ')
            if confirm != 'YES':
                print('Anulowano.')
                return

        try:
            deleted = query.delete(synchronize_session=False)
            db.session.commit()
            print(f'Udało się usunąć {deleted} posta(ów).')
        except Exception as e:
            db.session.rollback()
            print('Wystąpił błąd podczas usuwania:', e)
            sys.exit(1)


if __name__ == '__main__':
    main()

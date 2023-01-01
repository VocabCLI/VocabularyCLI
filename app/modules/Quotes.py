import typer
import contextlib
from Exceptions import *
from Database import createConnection, createTables
from datetime import datetime, timedelta
from pathlib import Path
from sqlite3 import *
import requests
from typing import *
from rich import print
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


# TODO: @anay - add rich themes, styling, formatting, emojis for almost every print statement. 
# TODO: @anay - Remove Panel.fit() and replace it with Panel() where message text varies. For errors let it be Panel.fit().

def get_quotes() -> List[Tuple]:
    """Returns a list of quotes from the database."""
    conn = createConnection()
    c = conn.cursor()
    c.execute("SELECT * FROM quotes")
    quotes = c.fetchall()

    # raise NoQuotesError if there are no quotes in the database
    with contextlib.suppress(NoQuotesException):
        if len(quotes) == 0:
            raise NoQuotesException

        print(
            Panel.fit(
                title="[b reverse green]  Your Quotes  [/b reverse green]", renderable=f"You have [bold green]{len(quotes)}[/bold green] quotes saved. 📚", title_align="center", padding=(1, 1)
            ))
        for quote in quotes:
            quote_text = quote[0]
            quote_author = quote[1] if quote[1] is not None else "-"
            quote_date = datetime.datetime.strptime(quote[2], '%Y-%m-%d %H:%M:%S').strftime('%d %b \'%y | %H:%M')

            # TODO: @anay, convert this to table
            print(
                f"[bold green]Quote:[/bold green] \"{quote_text}\" [bold green]Author:[/bold green] {quote_author} [bold green]Date:[/bold green] {quote_date}")


def add_quote(quote: str, author: Optional[str] = None):
    # sourcery skip: remove-redundant-fstring
    """_summary_

    Args:
        quote (str): _description_
        author (Optional[str]): _description_
    """

    conn = createConnection()
    c = conn.cursor()

    # strip the quote and author of any leading or trailing whitespace
    quote = quote.strip()

    # remove the quotes from the quote if they exist
    if quote.startswith('"') and quote.endswith('"'):
        quote = quote[1:-1]

    # remove the quotes from the quote if they exist
    if author and author.startswith('"') and author.endswith('"'):
        author = author[1:-1]

    # check if the quote does not only have whitespace
    if not quote:
        print(
            Panel.fit(
                title="[b reverse red]  Error!  [/b reverse red]",
                title_align="center",
                padding=(1, 1),
                renderable=f"[bold red]Quote[/bold red] cannot be empty. ❌",
            )
        )
        return

    if author and len(author.strip()) == 0:
        print(
            Panel.fit(
                title="[b reverse red]  Error!  [/b reverse red]",
                title_align="center",
                padding=(1, 1),
                renderable=f"[bold red]Author[/bold red] cannot have only whitespaces. ❌",
            )
        )
        return

    # check if the quote already exists in the database
    c.execute("SELECT * FROM quotes WHERE quote=?", (quote,))
    if c.fetchone() is not None:
        print(
            Panel.fit(
                title="[b reverse red]  Error!  [/b reverse red]",
                title_align="center",
                padding=(1, 1),
                renderable=f"[bold red]Quote:[/bold red] [bold blue]{quote}[/bold blue] already exists in your list. 📚",
            )
        )
        return


    # insert the quote into the database
    c.execute("INSERT INTO quotes VALUES (?,?,?)", (quote, author,
              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

    # print a success message
    print(
        Panel(
            title="[b reverse green]  Quote Added  [/b reverse green]",
            title_align="center",
            padding=(1, 1),
            renderable=f"[bold green]Quote:[/bold green] {quote} ✔")
    )


def search_quote(quoteText: str):
    """_summary_

    Args:
        quote (str): _description_
    """
    conn = createConnection()
    c = conn.cursor()

    # strip the quote of any leading or trailing whitespace
    quoteText= quoteText.strip()
    
    # convert the quote to lowercase so as to match the case of the quotes in the database
    quoteText = quoteText.lower()

    # remove the quotes from the quote if they exist
    if quoteText.startswith('"') and quoteText.endswith('"'):
        quoteText = quoteText[1:-1]

    # check if the quote does not only have whitespace
    if not quoteText:
        print(
            Panel.fit(
                title="[b reverse red]  Error!  [/b reverse red]",
                title_align="center",
                padding=(1, 1),
                renderable="[bold red]Search Text[/bold red] cannot be empty. Search with a few words. ❌",
            )
        )
        return

    # search for the quote in the database whiile LOWERING all the quotes in the database
    c.execute("SELECT * FROM quotes WHERE LOWER(quote) LIKE ? OR LOWER(author) LIKE ?", (f'%{quoteText}%',f'%{quoteText}%'))
    quotes = c.fetchall()

    # if the quote does not exist
    if quotes is None:
        print(
            Panel.fit(
                title="[b reverse red]  Error!  [/b reverse red]",
                title_align="center",
                padding=(1, 1),
                renderable=f"The quote with the words [bold red]{quoteText}[/bold red] does not exist in your list. 📚",
            )
        )
        return
            

    print(f"Found {len(quotes)} quotes with the words [u b]{quoteText}[/u b]")
    for quote in quotes:
        # print the quote
        quote_text = quote[0]
        quote_author = quote[1] if quote[1] is not None else "-"
        quote_date = datetime.datetime.strptime(quote[2], '%Y-%m-%d %H:%M:%S').strftime('%d %b \'%y | %H:%M')

        # TODO: @anay, convert this to table
        print(
            f"[bold green]Quote:[/bold green] \"{quote_text}\" [bold green]Author:[/bold green] {quote_author} [bold green]Date:[/bold green] {quote_date}"
            )


def delete_quote():
    """_summary_"""
    conn = createConnection()
    c = conn.cursor()
    c.execute("SELECT * FROM quotes ORDER BY quote ASC")
    quotes = c.fetchall()

    # raise NoQuotesError if there are no quotes in the database
    with contextlib.suppress(NoQuotesException):
        if len(quotes) == 0:
            raise NoQuotesException

        print(
            Panel.fit(
                title="[b reverse green]  Delete Quote  [/b reverse green]",
                renderable=" Select a quote to delete",
                title_align="center",
                padding=(1, 1),
            )
        )

        # display added quotes
        for idx, quote in enumerate(quotes, start=1):
            quote_num=idx
            quote_text = quote[0]
            quote_author = quote[1] if quote[1] is not None else "-"
            quote_date = quote[2]

            print(
                f'{quote_num}. [bold green]Quote:[/bold green] \"{quote_text}\" [bold green]Author:[/bold green] {quote_author} [bold green]Date:[/bold green] {quote_date}'
            )
        # prompt the user to select a quote index to delete
        quoteToDelete = input("Enter the index of the quote you want to delete: ")

        # check if the quoteToDelete is a number
        if not quoteToDelete.isdigit():
            print(
                Panel.fit(
                    title="[b reverse red]  Error!  [/b reverse red]",
                    title_align="center",
                    padding=(1, 1),
                    renderable=f"[bold red]Index:[/bold red] [bold blue]{quoteToDelete}[/bold blue] is not a number. ❌",
                )
            )
            return

        # check if the quoteToDelete is within the range of the quotes
        if int(quoteToDelete) not in range(1, len(quotes)+1):
            print(
                Panel.fit(
                    title="[b reverse red]  Error!  [/b reverse red]",
                    title_align="center",
                    padding=(1, 1),
                    renderable=f"[bold red]Index:[/bold red] [bold blue]{quoteToDelete}[/bold blue] is out of range. ❌",
                )
            )
            return

        # delete the quote from the database
        c.execute("DELETE FROM quotes WHERE quote=?", (quotes[int(quoteToDelete)-1][0],))
        print(Panel.fit(title="[b reverse green]  Quote Deleted  [/b reverse green]", renderable=f" Quote [bold green]{quoteToDelete}[/bold green]: {quotes[int(quoteToDelete)-1][0]} deleted successfully", title_align="center", padding=(1, 1)))
        conn.commit()
        
def get_random_quote():
    """_summary_"""
    conn = createConnection()
    c = conn.cursor()
    c.execute("SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1")
    random_quote = c.fetchall()[0]

    # raise NoQuotesError if there are no quotes in the database
    with contextlib.suppress(NoQuotesException):
        if len(random_quote) == 0:
            raise NoQuotesException

    
        # print the quote
        quote_text = random_quote[0]
        quote_author = random_quote[1] if random_quote[1] is not None else "-"
        quote_date = random_quote[2]

        print(
            f"[bold green]Quote:[/bold green] \"{quote_text}\" [bold green]Author:[/bold green] {quote_author} [bold green]Date:[/bold green] {quote_date}"
            )
        
def get_quote_of_the_day():
    """Get a random quote from a public API"""
    # get the quote of the day from the API
    quote = requests.get("https://quotes.rest/qod?language=en").json()["contents"]["quotes"][0]

    # print the quote
    quote_text = quote["quote"]
    quote_author = quote["author"] if quote["author"] is not None else "-"
    quote_date = quote["date"]
    quote_date=datetime.datetime.strptime(quote_date, '%Y-%m-%d').strftime('%d %b \'%y')

    # print using Panel
    print(
        Panel.fit(
            title=f"[b reverse green]  Quote of the Day - {quote_date} [/b reverse green]",
            renderable=f"[bold green]Quote:[/bold green] \"{quote_text}\" \n\n[bold green]Author:[/bold green] {quote_author}",
            title_align="center",
            padding=(1, 1),
        )
    )


def delete_all_quotes():
    """_summary_"""
    conn = createConnection()
    c = conn.cursor()
    c.execute("SELECT * FROM quotes ORDER BY quote ASC")
    quotes = c.fetchall()

    # raise NoQuotesError if there are no quotes in the database
    with contextlib.suppress(NoQuotesException):
        if len(quotes) == 0:
            raise NoQuotesException

        print(
            Panel.fit(
                title="[b reverse red]  Delete All Quotes  [/b reverse red]",
                renderable="⚠ [bold red]Warning:[/bold red] This action cannot be undone. Are you sure you want to delete all quotes?",
                title_align="center",
                padding=(1, 1),
            )
        )

        # prompt the user to select a quote index to delete
        print("")
        
        
        if typer.confirm(""):
            c.execute("DELETE FROM quotes")
            print(
                Panel.fit(
                    title="[b reverse green]  All Quotes Deleted  [/b reverse green]",
                    renderable="All quotes deleted successfully",
                    title_align="center",
                    padding=(1, 1),
                )
            )
            conn.commit()
        else:
            print(
                Panel.fit(
                    title="[b reverse green]  Your Quotes remain safe!  [/b reverse green]",
                    renderable="None of the quotes were deleted",
                    title_align="center",
                    padding=(1, 1),
                )
            )
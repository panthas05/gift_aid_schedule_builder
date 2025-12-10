# Gift aid schedule builder

A script to automate the building of gift aid schedule spreadsheets, as
specified
[here](https://www.gov.uk/guidance/schedule-spreadsheet-to-claim-back-tax-on-gift-aid-donations).

With kudos to Jenni, whose
[guide](https://www.girlguidingleicestershire.org/wp-content/uploads/gift-aid-1st-paxton.pdf)
was very helpful for clarifying certain facets of the gift aid schedule. Her
guide may prove to be a helpful document to have handy alongside this readme.

The Church of England also provides a
[guide](https://www.churchofengland.org/sites/default/files/2020-10/Claiming-Online-December-2019.pdf)
to making gift aid claims, which may also be helpful to peruse.

## How it works

The idea of this script is that you drop a bunch of bank transactions into this
folder under a file named `transactions.csv`, and a bunch of information about
all your gift aid donors under a file named `declarations.csv`. In
`declarations.csv`, you'll provide some way of identifying whether or not a bank
transaction is from a donor. The script will then check all the rows in
`transactions.csv`, pull out any which could have been from a donor listed in
`declarations.csv`, and write them into a gift aid schedule for you.

The script runs entirely locally - you can check the code for yourself to verify
that it doesn't post off your donor's data/your transactions anywhere! On a high
level, it doesn't even install the `requests` module (and I lack the willpower
to use `urllib` to make network requests).

> In `declarations.csv`, you'll provide some way of identifying whether or not a
bank transaction is from a donor.

Fleshing this out a bit, in `declarations.csv`, one of the columns will have the
title "Identifier". As you enter the donor declarations rows, enter into the
identifier column a _substring_ of the reference that appears on their bank
transactions.

By way of example, say you had a donor, whose bank transactions had the
following references:
- FP John Smith Giving Jan 2024
- FP John Smith Giving Feb 2024
- FP John Smith Giving Mar 2024

In the identifier column, you could put "FP John Smith Giving", and the script would
be able to catch all of the above transactions. This is similar to QuickBook's
"contains" matcher for when you're making a rule.

## Getting set up

Please ensure you have python 3.11+ installed (this script might work on lower
python versions, but that's untested). I wrote the script on linux, but I think
it should work on mac and windows too - please open an issue/PR if it doesn't.

If you use linux or mac, you should be able to run `./scripts/set_up.sh`, and
it'll configure everything for you. If that script doesn't work for whatever
reason, please use the following steps:
1. Create a virtual environment using your favourite method to do so (e.g.
   `python -m venv env`)
2. Activate the virtual environment (`source env/bin/activate`) and install
   dependencies listed in `./requirements/base.txt` by running `python3 -m pip
   install -r requirements/base.txt`
3. Copy `transactions.csv` and `declarations.csv` from the `templates/` folder
   into the project's root folder (i.e. the one which this README is in).
4. Create a folder in the project's root folder called `outputs/`

## How to use

In the below, all dates should be provided in the UK format of dd/mm/yy. This is
an edge case when ISO-8601 is inappropriate. ;) Please ensure too that the csv
files have UTF-8 encoding (I believe you can specify this during the "Save as"
stage in both excel and libreoffice).

### Setting up and running the script

Populate `transactions.csv` with transactions from your bank that you want to
process into a gift aid schedule (you can probably export a csv from your online
banking and rework it so it only has columns "Date", "Reference", and "Amount").
Not every transaction has to be gift-aidable (the script will ignore
transactions which it cannot match up to a declaration), so you can just do a
batch export for a time period and let the script filter out the gift-aidable
ones for you.

Transactions.csv could look something like this:

| Date      | Reference                     |   Amount  |
|-----------|-------------------------------|-----------|
| 01/01/24  | FP John Smith Giving Jan 2024 | £123.00   |

Populate `declarations.csv` with data about the gift aid declarations you have.
"Title" should be no more than 4 characters long (as per gov.uk's
[guidance](https://www.gov.uk/guidance/schedule-spreadsheet-to-claim-back-tax-on-gift-aid-donations#what-to-include)).
"First Name", "Last Name", "House Number or Name", and "Postcode" are hopefully
self-explanatory - postcodes are checked as the scripts run, and if one fails
validation it'll let you know. "Date" is the date that the declaration was
signed/made. Use the columns "Valid Four Years Before Day of Declaration",
"Valid Day of Declaration", and "Valid After Day of Declaration" to indicate
when the declaration is valid according to what the donor indicated. If a
declaration is valid in that time period, put a "1" in the column. If it's not,
put a "0" in the column. Finally, in the "Identifier" column, put some string
for the script to use to locate transactions by the donor.

Continuing our example, imagine John had submitted a declaration which wasn't
valid for the four years preceeding the declaration date, but was on the day of
the declaration, and afterwards too. Then, `declarations.csv` might look
something like this:

|Title|First Name|Last Name|House Number or Name|Postcode|Date|Valid Four Years Before Day of Declaration|Valid Day of Declaration|Valid After Day of Declaration|Identifier|
|-|-|-|-|-|-|-|-|-|-|
||John|Smith|Buckingham Palace|SW1A 1AA|25/12/23|0|1|1|FP John Smith Giving|

The script will run some checks on `transactions.csv` and `declarations.csv` as
it runs, and will let you know if any of the inputted data looks incorrect (e.g.
if a postcode doesn't match the usual UK format, or if one of the validity
columns has anything other than a "0" or a "1" in it).

Finally, once you've finished setting up your csvs, run `python3
gift_aid_schedule_builder.py`, and let the script do its magic!

Do note, gift aid schedules can only hold a maxiumum of 1000 transactions. The
script will warn you if you hit this limit, in which case you'll need to delete
some of the rows from `transactions.csv` (the script will tell you which), and
run the script again to generate another schedule.

### After the script has run

Each time the script runs, it creates a new folder inside the `outputs/` folder.
That new folder will hold five different files:
 - A completed gift aid schedule (`gift_aid_schedule__libre_.xlsx`)
 - A list of transactions that may be gift aidable, but require attention
   (`transactions_that_need_manual_handling.txt`)
 - A log, detailing what was done with each row of transactions.csv
   (`transactions_log.txt`)
 - A copy of `transactions.csv`
 - A copy of `declarations.csv`

The last three are simply for auditing purposes - if you want to examine what
the script did with each row and its reasons for doing so, you can check the
contents of `transactions_log.txt`. Copies of `transactions.csv` and
`declarations.csv` are made for posterity (as you'll be entering new
transactions to `transactions.csv` the next time you run the script).

There are some situations where the script won't be able to determine which
donor a transaction came from. Consider a transaction with reference "FP Hannah
Jane Doe". Say you had two donors, one with identifier "FP Hannah Jane", and
another with identifier "Jane Doe". Both identifiers would match the
transaction, and so the script would know that the transaction was gift aidable,
but wouldn't know which donor to assign to the transaction. When this happens,
the script will still write a row in the schedule for the transaction, but won't
provide any donor details on the row - only the amount. It will also leave a
note in `transactions_that_need_manual_handling.txt`, indicating which row of
the gift aid schedule needs attention, the possible donors that the donation
could have been from, and the original row of the transaction in
`transactions.csv`. You'll need to manually resolve such ambiguities before you
submit the schedule.

Finally, the star of the show, `gift_aid_schedule__libre_.xlsx`. This is the
schedule itself, which you'll upload to the HMRC government gateway. You'll need
to open this file in excel/libreoffice and save it as an `.ods` file before you
upload it. *Please check the transactions that the script writes to the
schedule.* In matching by reference, it may erroneously pick up transactions
that aren't gift aidable (for example, a gift-aid donor making a donation on
behalf of someone else - find some other exceptions
[here](https://www.gov.uk/guidance/gift-aid-what-donations-charities-and-cascs-can-claim-on#when-you-cannot-claim-gift-aid)).
Please remove any of these from the schedule before submitting it. The author of
the script provides no guarantee that the script will only pick out legitimately
gift-aidable transactions (see disclaimer below).

## Doing development

Contributions are most welcome! Some avenues for improvement can be found within
this section. The script `./scripts/init_dev_env.sh` will set up a development
environment for you, including `mypy` and `black` (please ensure any PR's are
formatted with `black` and fully typed - the precommit hook that the script
creates will reformat your changes with `black`, and typecheck them with `mypy`
to flag up any issues).

### Tests

Run tests with `python -m unittest discover .` - please ensure any PR's made
have test coverage (within reason, of course).

### Avenues for improvement

#### Add option of using excel spreadsheet

I used the libreoffice spreadsheet from the gov.uk website because I don't have
excel, but it'd be good if it could write to either spreadsheet depending on
what the user wanted. I guess we'd want to tweak the script to take a flag,
something like `python3 gift_aid_schedule_builder.py --output=excel`, which the
user could use to specify the output they want. It should probably default to
excel if not provided - I guess excel is more popular than libreoffice?

#### Better validation as per gov.uk page

On the gov.uk page, a length constraints are put on the "title", "first name",
and "last name" columns. It'd be good if the `declarations.csv` parsing could
validate these lengths are correct as it parses the file. In practice, this will
looks like throwing some more `DeclarationRowParsingError`s in
`DeclarationRow.from_row` in `./logic/parsing/parse_declarations_csv.py`.

Generally review the contents of the gov.uk page, and see what additional
validation we can do, as per their requirements.

#### Handle non-UK postcodes

Non-UK resident donors can still have their transactions gift aided. An "X"
should be put in the postcode column for them.

#### Output directly to an ods file

`openpyxl` is wonderful, but I believe it only supports .xlsx files. Is there
another package that can write .ods files? Or maybe one that can convert .xlsx
to .ods?

#### Make easier for non-technical users

Inevitably, a python script is going to bring with it a level of complexity,
which will make it a bit inaccessible for non-technical users. How can we make it
easier for non-technical users to use?

Low hanging fruit will probably be this readme - could it be made more
readable/accessible?

Less low hanging fruit, but probably of bigger impact - could this be rewritten
in dart then turned into an app with flutter? Or rewritten in javascript + rust
then turned into an app with tauri?

## Disclaimer

This script is a tool to make it easier to submit gift aid schedules, but it may
make errors, and shouldn't be used blindly. After it has built a schedule,
please undertake due dilligence to check the schedule, and verify that the
information it holds is correct.

The author of the script does not guarantee that the script is free from
defects. The script is provided "as is", and you use it at your own risk.

The author of the script makes no warantees as to performance, merchantability,
fitness for a particular purpose, or any other warranties whether expressed or
implied.

No oral or written communication from or information provided by the author of
the script shall create a warranty. Under no circumstances shall the author of
the script be liable for direct, indirect, special, incidental, or consequential
damages resulting from the use, misuse, or inability to use this software, even
if the author of the script has been advised of the possibility of such damages.

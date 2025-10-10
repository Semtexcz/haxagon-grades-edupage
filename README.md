# haxagon-grades-edupage

Automatizované skripty nad EduPage postavené na Playwrightu. Projekt poskytuje CLI, které umí znovupoužít přihlášení a spouštět jednotlivé scénáře (např. otevření známek nebo vytvoření nové písemky) bez nutnosti ručních kliků.

## Přehled
- využívá Playwright (Firefox) pro automatizaci prohlížeče
- CLI stojí na knihovně `click`
- přihlášení se ukládá do `auth.json`, aby nebylo nutné se pokaždé přihlašovat
- logování probíhá přes `loguru` (úroveň lze přepnout proměnnou `HAXAGON_LOG_LEVEL`)
- scénáře se registrují přes `Scenario` base class a lze je snadno rozšiřovat

## Požadavky
- Python 3.13+
- [Poetry](https://python-poetry.org/) (doporučeno) nebo jiný nástroj pro správu virtuálního prostředí
- Nainstalované Playwright prohlížeče (projekt využívá Firefox)

## Instalace
```bash
# 1) vytvoření a aktivace virtual env přes Poetry
poetry install

# 2) stažení ovladačů pro Playwright (alespoň Firefox)
poetry run playwright install firefox
```

Alternativně bez Poetry: `python -m venv .venv && source .venv/bin/activate && pip install -e .` a pak `playwright install firefox`.

### Instalace přes pipx z GitHubu
Pokud chcete nástroj používat jako globální CLI bez ruční správy virtuálního prostředí, nainstalujte jej přes [pipx](https://pipx.pypa.io/):

```bash
# jednorázová instalace přímo z GitHubu
pipx install "git+https://github.com/Semtexcz/haxagon-grades-edupage.git"

# stažení Playwright prohlížeče (spustí se v pipx prostředí balíčku)
pipx run --spec "haxagon-grades-edupage" playwright install firefox

# ověření instalace
haxagon-grades-edupage --help
```

Aktualizace na poslední verzi z repozitáře: `pipx install --force "git+https://github.com/Semtexcz/haxagon-grades-edupage.git"`.

## Konfigurace
Před prvním přihlášením je potřeba předat přihlašovací údaje přes proměnné prostředí:

```bash
export EDUPAGE_USERNAME="uzivatel@skola.cz"
export EDUPAGE_PASSWORD="tajne-heslo"
# volitelné: základní URL, pokud není https://1itg.edupage.org/
# export EDUPAGE_URL="https://skola.edupage.org/"
```

Příkaz `login` uloží stav session do `auth.json` v kořeni projektu. Pokud soubor odstraníte nebo session vyprší, stačí `login` spustit znovu.

## CLI
CLI se spouští jako modul:

```bash
poetry run python -m haxagon_grades_edupage.cli --help
```

### Rychlý start
```bash
# vypsat dostupné scénáře
poetry run python -m haxagon_grades_edupage.cli list

# přinutit nové přihlášení + uložit session
poetry run python -m haxagon_grades_edupage.cli login

# spustit scénář na vytvoření písemky
poetry run python -m haxagon_grades_edupage.cli create-task --class "3.gpu" --task "Test 1:50" --task "Opakování:30"

# otevřít stránku se známkami pro daný školní rok
poetry run python -m haxagon_grades_edupage.cli grades --year 2025
```

### Dostupné scénáře
- `grades` – otevře EduPage sekci se známkami a přepne na zvolený školní rok.
- `create-task` – hromadně vytvoří písemky/zkoušení pro zadanou třídu a předmět.

Každý scénář je implementován ve složce `src/haxagon_grades_edupage/scenarios/` a registruje vlastní CLI příkaz přes metodu `register_cli`.

#### Vytvoření písemek (`create-task`)

Scénář očekává třídu (`--class`) a volitelně název předmětu (`--subject`, výchozí *Informatika*). Písemky lze předat několika způsoby:

- jednotlivě přes dvojici `--name/--points`
- hromadně na CLI pomocí opakovaného `--task "Název:Body"`
- z CSV souboru pomocí `--task-csv path/to/tasks.csv`

CSV musí mít hlavičku se sloupci `name`/`task` a `points`/`body`. Ukázka:

```csv
name,points
Test kapitola 1,25
Opakování,15
```

Scénář se pokusí přeskočit již existující písemky (po doplnění selektoru `TASK_ROW_LOCATOR` přímo v `create_task.py`).

## Vývoj
- Sdílená logika pro práci se session je v `src/haxagon_grades_edupage/auth_manager.py`.
- Nový scénář vytvoříte děděním z `Scenario` (`base.py`) a přidáním do seznamu `SCENARIOS` v `cli.py`.
- Pro inspiraci je zde `create_task.py`, původní záznam Playwright Codegen – slouží jen jako reference.

Doporučený postup vývoje:
1. Spustit `poetry run playwright codegen <url>` a nahrát kroky.
2. Kód upravit/učistit a přesunout do nového scénáře.
3. Zaregistrovat scénář v `cli.py` a (pokud dává smysl) přidat volby do CLI.

## Tipy pro ladění
- Nastavení `slow_mo` nebo `headless=False` je již použito ve scénářích – Playwright tak kroky vizuálně předvádí.
- Pokud Playwright hlásí chybu přihlášení, smažte `auth.json` a znovu spusťte `login`.
- Ukládání session je citlivé – zacházejte s `auth.json` jako s tajným souborem.

## Struktura repozitáře
```
├─ src/haxagon_grades_edupage/
│  ├─ cli.py                # registrace a spouštění CLI scénářů
│  ├─ auth_manager.py       # práce se session a přihlášením
│  ├─ setup_login.py        # plný přihlašovací flow + uložení auth.json
│  ├─ scenario_runner.py    # helper pro spuštění scénáře s Playwrightem
│  └─ scenarios/            # jednotlivé scénáře (grades, create_task, ...)
├─ tests/                   # místo pro testy (aktuálně prázdné)
├─ auth.json                # uložená session (vytvoří se po loginu)
├─ pyproject.toml           # konfigurace balíčku
└─ README.md
```

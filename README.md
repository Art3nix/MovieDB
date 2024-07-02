# MovieDB

## Požadavky

### Python

Není potřeba instalovat lokálně Python, protože je již v Dockeru. Aplikace používá verzi 3.10.

### Docker

Lokálně je nutné mít nainstalovaný pouze Docker včetně Docker compose.

### Requirements

Další dependencies projektu jsou vypsány v souboru `requirements.txt`.
## Návod na spuštění

Projekt je rozdělen do následujících Docker containerů:
- db - container spravující databázi filmů a uživatelů
- web - webová aplikace
- pgadmin - externí nástroj pro manuální úpravu dat v databázi


### Projekt

Po naklonování repozitáře lze aplikaci spustit pomocí příkazu `docker compose up [-d]`. Příkazem se spustí celá aplikace včetně databáze. Přepínač `-d` spustí projekt na pozadí.

Vypnout aplikaci lze například pomocí CTRL+C.

K aplikaci lze přistupovat na adrese `http://127.0.0.1:8000/`.

## Testování

Podle způsobu testování se také musí změnit nastavení pytestů v `tests/conftest.py`.

Pro lokální testování musí být ve funkci `test_client()` nastavená config_class takto:
`test_app = create_app(config_class=config.LocalTestingConfig)`.

Pro testování uvnitř Docker containeru musí mít funkce `test_client()` nastavenou config_class takto:
`test_app = create_app(config_class=config.DockerTestingConfig)`.

### Testování v lokálním prostředí pomocí venv

Nejprve si vytvořte virtuální prostředí příkazem `python -m venv .venv` a aktivujte ho pomocí `source .venv/bin/activate`. 
Poté nainstalujte dependencies `pip install -r requirements.txt`.

Testy lze poté spustit pomocí příkazu `python -m pytest tests/`.

Pro detailnější statistiky včetně pokrytí lze spustit tento příkaz: `python -m pytest tests/ --cov=semwork --cov-report term-missing`.

### Testování uvnitř Docker containeru

Pokud nechcete vytvářet virtuální prostředí lze spustit testy rovnou v Docker containeru. Po spuštění aplikace lze uvnitř containeru spustit testy
pomocí příkazu `docker exec -it semwork-web-1 python -m pytest tests/`.

Pro detailnější statistiky vypadá příkaz následovně `docker exec -it semwork-web-1 python -m pytest tests/ --cov=semwork --cov-report term-missing`.
SYSTEM_PROMPT = """\
Ti si AI-agent za nekretnine koji komunicira sa klijentima u Telegramu na \
srpskom jeziku. Tvoj cilj je da vodiš živ, prirodan razgovor (a ne samo da \
popunjavaš upitnik) i postepeno saznaš parametre klijentovog zahteva:
- tip posla: kupovina, zakup ili prodaja;
- grad i opština/kvart;
- tip objekta: stan, kuća, poslovni prostor, zemljište;
- broj soba;
- budžet (minimum/maksimum, valuta);
- broj telefona za kontakt.

Pravila ponašanja:
1. Komuniciraj toplo, kratko i jasno, kao iskusan agent-konsultant.
2. Postavljaj jedno-dva potpitanja odjednom, a ne celu listu odjednom.
3. Čim klijent navede bilo koju strukturiranu informaciju (grad, \
budžet, broj soba, tip posla, telefon itd.) — obavezno pozovi \
alat update_lead_profile, čak i ako je informacija delimična.
4. Kada su jasni hitnost zahteva i spremnost klijenta (na primer, već \
postoji konkretan budžet i telefon, ili klijent kaže "hitno", "želim već \
ove nedelje") — pozovi classify_lead da odrediš "temperaturu" leada \
(hot/warm/cold) i hitnost.
5. Trenutno sistem radi samo za Crnu Goru (Podgorica, Budva, Kotor, \
Tivat). Ako klijent pomene drugi grad — ljubazno ga upozori na ovo \
ograničenje.
6. Kada su svi ključni parametri prikupljeni (tip posla, grad, tip objekta, \
sobe, budžet, telefon), obavesti klijenta da ćeš odmah pronaći ponude, i ne \
postavljaj više potpitanja bez potrebe.
7. Ne izmišljaj konkretne adrese ili oglase sam — pronalaženjem ponuda \
bavi se poseban modul za pretragu.
"""

UPDATE_LEAD_PROFILE_TOOL = {
    "name": "update_lead_profile",
    "description": (
        "Sačuvaj ili ažuriraj strukturirane podatke o klijentovom zahtevu, "
        "dobijene iz razgovora. Pozovi svaki put kada saznaš novu vrednost "
        "bilo kog polja."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "deal_type": {
                "type": "string",
                "enum": ["buy", "rent", "sell"],
                "description": "Tip posla: kupovina, zakup ili prodaja",
            },
            "city": {"type": "string", "description": "Grad pretrage"},
            "district": {"type": "string", "description": "Opština/kvart grada"},
            "property_type": {
                "type": "string",
                "enum": ["apartment", "house", "commercial", "land"],
            },
            "rooms": {"type": "integer", "description": "Broj soba"},
            "budget_min": {"type": "integer", "description": "Minimalni budžet"},
            "budget_max": {"type": "integer", "description": "Maksimalni budžet"},
            "budget_currency": {"type": "string", "enum": ["USD", "UAH", "EUR"]},
            "phone": {"type": "string", "description": "Broj telefona klijenta"},
            "full_name": {"type": "string", "description": "Ime klijenta"},
        },
        "additionalProperties": False,
    },
}

CLASSIFY_LEAD_TOOL = {
    "name": "classify_lead",
    "description": (
        "Odredi 'temperaturu' leada i hitnost zahteva na osnovu celog "
        "razgovora. hot — klijent je spreman da odmah deluje (ima budžet, "
        "telefon, jasne kriterijume, pominje hitnost). warm — postoje "
        "osnovni kriterijumi, ali nema hitnosti ili potpunog skupa podataka. "
        "cold — nejasna potreba, rana faza, klijent 'samo gleda'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "temperature": {"type": "string", "enum": ["hot", "warm", "cold"]},
            "urgency": {
                "type": "string",
                "description": "Kratak opis hitnosti, npr. 'potrebno za 2 nedelje'",
            },
        },
        "required": ["temperature"],
        "additionalProperties": False,
    },
}

TOOLS = [UPDATE_LEAD_PROFILE_TOOL, CLASSIFY_LEAD_TOOL]

GREETING_MESSAGE = (
    "Zdravo! 👋 Ja sam AI-asistent za pronalaženje nekretnina. Pomoći ću vam "
    "da brzo pronađete ponudu po vašem zahtevu ili da prodate/iznajmite vaš "
    "objekat.\n\n"
    "Recite mi, molim vas, šta vas zanima: kupovina, zakup ili prodaja?"
)

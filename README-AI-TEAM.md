# AI Development Team + EMS specialists

Detta paket är en repo-lokal konfiguration för GitHub Copilot-baserad utveckling i VS Code och andra miljöer som läser `.github`-anpassningar. Det kombinerar det generella AI-utvecklingsteamet med tre energispecialister:

- **Energy Management System Expert**
- **Modbus Expert**
- **Home Assistant Expert**

Paketet är anpassat för ett lokalt EMS med Home Assistant, Python/AppDaemon, .NET, Docker, OR-Tools, Nord Pool, Solcast, GoodWe, SolarEdge, Solinteg och batterilagring. Exakta IP-adresser, firmware, register, entity-ID:n och effektgränser måste fyllas i och verifieras i respektive repository.

## Installation

1. Packa upp ZIP-filen.
2. Kopiera innehållet till repository-roten. Merge:a en befintlig `.github`-katalog; ersätt den inte blint.
3. Fyll i `docs/project/project-profile.md`.
4. Kör validering:

```powershell
pwsh ./scripts/validate-package.ps1
```

eller:

```bash
python3 ./scripts/validate_package.py
```

5. Öppna repository-roten i VS Code och kör `Developer: Reload Window`.
6. Starta med prompten `/onboard-repository` eller välj **Project Manager** och be om en read-only onboarding.

## Team

### Generella roller

1. Project Manager
2. Lead Architect
3. Backend Engineer
4. Frontend Engineer
5. Database Engineer
6. QA Engineer
7. Security Reviewer
8. DevOps Engineer
9. Code Reviewer

### EMS-specialister

10. Energy Management System Expert
11. Modbus Expert
12. Home Assistant Expert

## Rekommenderat arbetsflöde

```text
DISCOVER
→ REQUIREMENTS AND SAFETY CLASSIFICATION
→ ARCHITECTURE
→ SPECIALIST REVIEW
→ IMPLEMENTATION
→ TEST
→ SECURITY
→ FINAL REVIEW
→ HUMAN APPROVAL
```

För fysisk styrning används dessutom:

```text
READ-ONLY OBSERVABILITY
→ VERIFIED REGISTER/INTERFACE
→ SIMULATION
→ ARMED SIGNAL
→ LIMITED WRITE TEST
→ FEEDBACK VERIFICATION
→ ROLLBACK TEST
→ SOAK TEST
```

## Viktiga skyddsregler

- Gissa aldrig registeradresser, skrivvärden, firmwarekrav, CAN-pinout eller batteriprotokoll.
- Ingen Modbus-skrivning utan verifierad dokumentation, känt rollbackvärde och uttryckligt mänskligt beslut.
- Använd en enda anslutningsägare per fysisk Modbus-enhet.
- Definiera teckenkonvention och enheter innan formler eller automationer skapas.
- Börja med read-only observability och lägg fysisk styrning bakom en `enable/armed`-signal.
- AI-teamet får aldrig ensamt godkänna produktionssättning.

## Anpassning

Agentfilerna saknar avsiktligt hårdkodade verktygslistor. Verktygsnamn varierar mellan Copilot-versioner och agentmiljöer. Konfigurera verktyg per agent och använd least privilege. Ge inte generella roller direkt skrivåtkomst till Home Assistant, Modbus eller produktionsmiljö.

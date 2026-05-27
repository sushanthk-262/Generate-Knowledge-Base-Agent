---
applyTo: "Guides/**/*.md"
description: Domain overlay for Intel platform-security / BIOS / IFWI repos. Only applies when the repo's source material is about Intel platform security topics; otherwise these conventions are inert.
---

# Intel platform-security domain overlay

Apply these conventions **only** when the topic genuinely belongs to the Intel platform-security stack (Boot Guard, BIOS Guard, TXT, TPM/PCR, TME/MKTME, TDX, CSME/AMT, VTIO, HSTI, OCR/RPE, PSR, SPIRAL, IFWI/FSP, etc.). If the repo is about something else, ignore this file and follow only the base style file.

## Terminology — use these spellings exactly

| Write it as | Not as |
|---|---|
| Boot Guard (two words, both capitalized) | BootGuard, bootguard |
| BIOS Guard | BIOSGuard |
| TPM PCR (Platform Configuration Register) | TPM register |
| Initial Boot Block (IBB) / OEM Boot Block (OBB) | IBB code / OBB code |
| Authenticated Code Module (ACM) | ACM module |
| Key Manifest (KM) / Boot Policy Manifest (BPM) | manifest file |
| Field Programmable Fuses (FPFs) | fuse bits |
| Measured Launch Environment (MLE) | measured launch env |
| Trust Domain Extensions (TDX) | Trusted Domain Extensions |
| Converged Security and Manageability Engine (CSME) | Intel ME / CSE |

## Required framing for any security-feature guide

1. **Threat → Mitigation** is mandatory (replaces "Problem → Solution" for these guides).
2. Always state **where the root of trust lives**: silicon (fuses), an Intel-signed binary (ACM), the TPM, the CSME, or the OEM. A guide that doesn't answer "who do you have to trust for this to work?" is incomplete.
3. Always state **when in the boot/runtime timeline** the feature is active. Use this canonical timeline reference:
   ```
   Reset → uCode → Boot Guard ACM → IBB → OBB/PEI → DXE → BDS → OS loader → OS runtime
   ```
4. For features with multiple **profiles** (Boot Guard, BIOS Guard enforcement modes, TXT launch modes), include the full profile table — don't summarize it.

## TPM / measurement guides

- Always specify **which PCR** is extended and **what value** is extended into it.
- Use the standard PCR allocation table when relevant (PCR 0 = CRTM/POST BIOS, PCR 1 = platform config, …, PCR 7 = Secure Boot policy).
- Distinguish **verified boot** (signature check, halts on fail) from **measured boot** (hash → PCR extend, never halts). Newcomers confuse these constantly.

## Confidential-compute guides (TDX, MKTME, SGX-adjacent)

- Always state the **trust boundary** explicitly: who is inside the TCB, who is outside.
- Always state the **key lifecycle**: where the key is generated, where it lives, who can request it, when it is destroyed.
- Distinguish **encryption** from **integrity** from **attestation** — each is a separate guarantee.

## CSME / AMT / manageability guides

- Always state whether the feature works **with the main CPU powered off** (S5/Sx) or only at runtime.
- Distinguish **in-band** (OS-mediated) from **out-of-band** (CSME-only) operations.

## Cross-references newcomers always need

Whenever a guide mentions any of these, link to the indicated guide on first mention:

| Mention of … | Link to |
|---|---|
| ACM, IBB, OBB, KM, BPM | `01-boot-guard-and-acm.md` |
| flash update, PFAT | `02-bios-guard.md` |
| PCR, attestation, measured boot | `03-tpm-and-measurements.md` |
| MLE, SENTER, SINIT | `04-txt-and-mle.md` |
| TME, MKTME, memory encryption key | `05-memory-encryption.md` |
| TD, Trust Domain, TDX module | `06-tdx.md` |
| CSME, AMT, OCR, RPE, PSR | `08-csme-amt-ocr-rpe.md` |

## Sources to prefer (when both exist)

1. Official Intel BIOS Writer's Guide (BWG) terminology > internal slide deck terminology > video transcript wording.
2. If a transcript and a slide contradict, trust the slide and flag the discrepancy in `Guides/_sources.md`.

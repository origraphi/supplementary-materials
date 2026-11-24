# 3 Expert study

Sessions with experts who explored the Origraphi demo (see `../demo/`) on three example networks
(company, logistics and trading network) while thinking aloud. The experts saw unfolded,
(edge-)folded and fully folded versions; the fully folded version is described in the paper.
The sessions were held in German.

## Contents

| Path                                       | Contents                                        |
|--------------------------------------------|-------------------------------------------------|
| `interviews/original_de/`                  | Transcripts in the original German (7 sessions) |
| `interviews/translated_en/`                | English machine translations of the transcripts |
| `coding/anonymous_raccoon_<n>.<date>.xlsx` | Notes per session (one file per transcript)     |
| `coding/qualitative.xlsx`                  | Thematic coding of quotes across sessions       |

Files are named `anonymous_raccoon_<n>.<yyyymmdd>`: a pseudonym for the expert and the date of the
session. A transcript, its translation and its notes share the same name; translations end in `_en`.

## Transcription

The audio recordings were transcribed **locally** with
[noScribe](https://github.com/kaixxx/noScribe) (version 0.7), so no recording left our machines.
noScribe builds on OpenAI's Whisper (through faster-whisper) for speech recognition and on pyannote
for telling speakers apart. Settings, as recorded in each transcript's header: language German,
2 speakers, overlapping speech, timestamps, disfluencies and pauses marked.

Transcript notation:

| Notation                            | Meaning                          |
|-------------------------------------|----------------------------------|
| `S00:`, `S01:`                      | Speaker, as detected by noScribe |
| `[hh:mm:ss]`                        | Time stamp in the recording      |
| `(.)`, `(..)`, `(10 seconds pause)` | Pauses                           |
| `//S01: …//`                        | Overlapping speech               |
| `ähm`, `mhm`, …                     | Disfluencies, kept as spoken     |

Transcripts were checked for identifying details; the few names mentioned are replaced with
`[name redacted]`. `[Origraphi]` marks where the project's earlier working name was replaced. The recordings themselves are not shared.

## Translation

The German transcripts were translated to English **locally** with
[translateLocally](https://github.com/XapaJIaMnu/translateLocally), using its German→English model
from the [Bergamot project](https://browser.mt) (models: [browsermt/students](https://github.com/browsermt/students)).
The translations are unedited machine output: they follow the original line by line, but contain
translation errors, especially for spoken German and for transcription errors in the original.
Where the two versions differ, the German original is the reference, and all quotes in the paper
were checked against it.

## Coding

**Notes per session** (`coding/anonymous_raccoon_<n>.<date>.xlsx`): one row per observation, 157 in total.

| Column      | Contents                                                      |
|-------------|---------------------------------------------------------------|
| `Timestamp` | Position in the recording                                     |
| `Dataset`   | Network being explored: Company, Logistics or Trading Network |
| `Type`      | `visualization`, `data`, `feature` (request or idea) or `bug` |
| `Note`      | The observation, in English                                   |

**Thematic coding** (`coding/qualitative.xlsx`): one row per quote. Columns: `interviewee`,
`timestamp`, `comment` (the quote), then one column per code; an `x` marks that the code applies.
Row 104 counts the marks per code over the expert sessions (rows 17–103). Rows labelled `pilot`
are from a pilot session and are not counted. Quotes are from the English translations, except for
interviewee 1, whose quotes were translated by hand from the German original because the machine
translation of that session is too garbled to quote.

Codes: staircase collapse makes sense · node group collapse makes sense · information loss is
acceptable · hierarchical ordering supported · overview / information at a glance · collapsing
addresses network density/size · half collapse better than full collapse · adaptive/focus+context
collapse? · collapsing affects path-tracing/routes · inferences about data / behavior · unclear /
ambiguous encoding or interaction.

The coding uses the working terms from the time of the sessions: *collapse* for folding, and
*half collapse* / *full collapse* for the (edge-)folded and fully folded views.
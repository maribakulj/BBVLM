# Offline XML validation

Unmodified schemas fetched on 2026-09-27:

- ALTO 4.4: https://raw.githubusercontent.com/altoxml/schema/master/v4/alto-4-4.xsd
- METS 1.12.1: https://raw.githubusercontent.com/mets/METS-schema/main/version1121/mets.xsd
- METS XLink schema v2 (15 November 2004), mirrored by OCR-D:
  https://raw.githubusercontent.com/OCR-D/core/master/src/ocrd_validators/xlink.xsd

The LoC XLink endpoint was blocked during this run. The matching legacy XLink
schema is resolved locally; no schema is weakened or rewritten. The W3C XLink
1.1 schema is not interchangeable with this dependency (`simpleLink`).

`bbvlm.formats.validate_xml` disables network access and fails when an imported
schema is missing. XSD conformance says nothing about transcription correctness.
Custom BBVLM metadata is permitted by METS `xmlData` and validated separately by
the graph checks, not by a MODS/PREMIS schema.

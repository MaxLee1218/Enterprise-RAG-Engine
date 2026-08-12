# Supplier Quality KPI Definitions

| Control Field | Value |
| --- | --- |
| Document ID | KPI-SQ-002 |
| Document Type | KPI Standard |
| Version | 1.4 |
| Effective Date | 2026-01-01 |
| Document Owner | Quality Analytics |
| Approved By | Director of Quality Systems |
| Classification | Internal |
| Business Function | Supplier Quality Analytics |
| Applicable Scope | Supplier Quality Analysis v1.1 and controlled management reporting |

Controlled document. Printed copies are uncontrolled unless stamped and dated by Document Control. This synthetic document contains no real company confidential information.

## 1. Purpose

This standard defines the deterministic Supplier Quality metrics currently supported by Supplier Quality Analysis v1.1. Its objective is to keep structured business data and unstructured policy knowledge semantically aligned.

## 2. Scope

The definitions apply to applicable incoming inspection records selected for a supplier and reporting period. Selection criteria, period boundaries, and completion status shall be applied consistently to numerator and denominator. Supplementary metrics not identified as supported are reference-only and shall not be presented as current deterministic system capability.

## 3. Definitions and Source Data

| Data Element | Meaning |
| --- | --- |
| supplier_id | Stable identifier of the supplier associated with the inspection record. |
| period | Approved reporting interval, normally a calendar or defined fiscal quarter. |
| total_quantity | Number of individual units inspected in one applicable incoming inspection record. |
| rejected_quantity | Number of those inspected units that failed acceptance criteria. |
| inspection record count | Number of database rows or inspection events; not an input to Inspected Count. |

## 4. Roles and Responsibilities

1. Quality Analytics owns formula governance, calculation versioning, and reproducibility controls.
2. Incoming Quality owns accurate total_quantity and rejected_quantity source records.
3. Supplier Quality owns business interpretation and confirms supplier and period scope.
4. Quality Systems resolves calculation defects or conflicts between controlled documents.

## 5. Supported KPI Definitions

### 5.1 Inspected Count

Inspected Count = SUM(total_quantity) for all applicable incoming inspection records.

Inspected Count measures individual inspected units. It does not mean the number of inspection records. If three applicable records contain total_quantity values of 400, 600, and 1,000, Inspected Count is 2,000 units, not 3 records.

### 5.2 Defect Count

Defect Count = SUM(rejected_quantity) for all applicable incoming inspection records.

Defect Count measures rejected inspected units. It shall use the same supplier, period, completion, site, and material scope as Inspected Count.

### 5.3 Defect Rate

Defect Rate = Defect Count / Inspected Count.

Equivalently, Defect Rate = SUM(rejected_quantity) / SUM(total_quantity) over the same applicable record set. If Inspected Count is zero, Defect Rate is not calculable; it is not 0.00%.

Example: Inspected Count is 10,000 units and Defect Count is 250 units. Defect Rate = 250 / 10,000 = 0.025 = 2.50%.

The calculated Defect Rate is used by SQM-001 for supplier performance classification and by QP-SQ-012 for rate-based escalation. It does not replace severity review under POL-SQ-007.

### 5.4 Period-over-Period Change

Period-over-period change = current period Defect Rate - previous period Defect Rate.

The result shall be reported in percentage points, not percent change. Example: Q1 Defect Rate is 2.00% and Q2 Defect Rate is 3.50%. Period-over-period change is +1.50 percentage points. A percent change calculation of 75% is a different measure and is not the supported v1.1 trend definition.

## 6. Classification Use

Decision Quick Reference: If Defect Rate is below 2%, performance is Acceptable. From exactly 2.00% through exactly 5.00%, Review is Required. When Defect Rate exceeds 5%, Corrective Action is Required. Exact boundary examples are: 1.99% is Acceptable; 2.00% is Review Required; 5.00% is Review Required; and 5.01% is Corrective Action Required.

| Calculated Defect Rate | SQM-001 Classification |
| --- | --- |
| Less than 2.00% | Acceptable |
| Greater than or equal to 2.00% and less than or equal to 5.00% | Review Required |
| Greater than 5.00% | Corrective Action Required |

Boundary examples: 1.99% is Acceptable; 2.00% is Review Required; 5.00% is Review Required; and 5.01% is Corrective Action Required.

### 6.1 Calculation Procedure and Data Controls

1. Identify supplier_id and the approved reporting period.
2. Select applicable completed incoming inspection records.
3. Confirm total_quantity and rejected_quantity are non-negative and rejected_quantity does not exceed total_quantity.
4. Sum total_quantity to obtain Inspected Count.
5. Sum rejected_quantity to obtain Defect Count.
6. Divide Defect Count by Inspected Count when the denominator is greater than zero.
7. Apply the exact boundary table in section 5.
8. When comparing periods, subtract the previous rate from the current rate and label the result in percentage points.
9. Preserve the record set or reproducible query reference used for the calculation.

## 7. Exceptions and Reference-only KPIs

Missing, duplicate, reversed, or unreconciled inspection quantities shall be resolved or explicitly excluded through an approved data-quality decision. Numerator and denominator scopes shall never be changed independently to improve a result.

The following are reference-only KPIs and are not currently calculated by Supplier Quality Analysis v1.1: supplier PPM, cost of poor quality, on-time corrective action closure, audit score, and process capability index. They require separate controlled definitions and data contracts before automation.

## 8. Governance and Escalation

Quality Analytics owns formula governance. Supplier Quality owns business interpretation. A suspected calculation defect, data-contract mismatch, or conflicting policy boundary shall be escalated to Quality Systems before publishing the affected management report.

## 9. Records and Evidence

Each reported KPI shall retain supplier_id, period, included record identifiers or a reproducible query reference, Inspected Count, Defect Count, Defect Rate, period comparison when used, calculation version, timestamp, and reviewer. Retention is seven years unless a longer schedule applies.

## 10. Related Documents

- SQM-001, Supplier Quality Manual
- QP-INSP-004, Incoming Inspection Procedure
- POL-SQ-007, Supplier Nonconformance Policy
- QP-SQ-012, Quality Escalation Procedure

## 11. Revision History

| Version | Effective Date | Change Summary | Approver |
| --- | --- | --- | --- |
| 1.3 | 2025-07-01 | Added common period scope and zero-denominator control. | Director of Quality Systems |
| 1.4 | 2026-01-01 | Clarified unit aggregation, percentage points, boundaries, and supported v1.1 capability. | Director of Quality Systems |

End of controlled document KPI-SQ-002, version 1.4.

# Supplier Quality Manual

| Control Field | Value |
| --- | --- |
| Document ID | SQM-001 |
| Document Type | Quality Manual |
| Version | 2.1 |
| Effective Date | 2026-01-01 |
| Document Owner | Global Supplier Quality |
| Approved By | Director of Quality |
| Classification | Internal |
| Business Function | Supplier Quality Management |
| Applicable Scope | Approved production, incoming material, and critical component suppliers |

Controlled document. Printed copies are uncontrolled unless stamped and dated by Document Control. This synthetic document contains no real company confidential information.

## 1. Purpose

This manual establishes the governing principles for selecting, monitoring, reviewing, and escalating suppliers whose material or components can affect product quality. It provides a common decision framework so that supplier performance decisions are evidence-based, traceable, and consistent across sites.

## 2. Scope

This manual applies to approved production suppliers, incoming material suppliers, and critical component suppliers. It applies to Supplier Quality, Incoming Quality, Procurement, Manufacturing Quality, and Quality Management personnel who evaluate supplier performance. It does not authorize an automated agent to create, approve, or close a corrective action; it defines the business policy that authorized personnel must apply.

## 3. Definitions

| Term | Controlled Definition |
| --- | --- |
| Inspected Count | Sum of individual units inspected, calculated as SUM(total_quantity) for applicable incoming inspection records. |
| Defect Count | Sum of rejected inspected units, calculated as SUM(rejected_quantity). |
| Defect Rate | Defect Count divided by Inspected Count, as defined in KPI-SQ-002. |
| Major Deviation | A nonconformance with material effect on fit, form, function, reliability, regulatory compliance, or approved process control. |
| Review Threshold | A defect rate greater than or equal to 2.00 percent. |
| Corrective Action Threshold | A defect rate greater than 5.00 percent. |
| Management Review | A documented leadership review of performance, risk, containment, and sourcing disposition. |

## 4. Roles and Responsibilities

1. Supplier Quality Engineer validates evidence, assigns the performance classification, and maintains the supplier quality record.
2. Incoming Quality records total_quantity and rejected_quantity at the unit level and links inspection evidence to the supplier and period.
3. Procurement participates in reviews that may affect sourcing, commercial commitments, or supplier status.
4. Quality Management approves formal escalations and chairs management review when required by QP-SQ-012.
5. Document Control maintains the active version and prevents superseded copies from being represented as current policy.

## 5. Supplier Performance Framework

Supplier performance shall be evaluated from incoming inspection results, defect rate, major deviations, repeated nonconformance, quality escalation history, open containment, and corrective action status. A single KPI shall not erase a material severity event. Evidence must be drawn from approved inspection records, deviation records, supplier performance reports, and controlled quality records.

Defect Rate shall be calculated according to KPI-SQ-002 using aggregated unit quantities, not the number of inspection records.

### 5.1 Defect Rate Classification

Decision Quick Reference: If Defect Rate is below 2%, performance is Acceptable. From exactly 2.00% through exactly 5.00%, Review is Required. When Defect Rate exceeds 5%, Corrective Action is Required and Level 2 escalation applies. Exact boundary examples are: 1.99% is Acceptable; 2.00% is Review Required; 5.00% is Review Required; and 5.01% is Corrective Action Required.

| Defect Rate | Classification | Required Response |
| --- | --- | --- |
| Less than 2.00% | Acceptable | Level 0 normal monitoring |
| Greater than or equal to 2.00% and less than or equal to 5.00% | Review Required | Level 1 supplier review |
| Greater than 5.00% | Corrective Action Required | Formal corrective action and Level 2 escalation |

The boundary values are intentional. A rate of 1.99% is Acceptable. A rate of 2.00% is Review Required. A rate of 5.00% is Review Required. A rate of 5.01% is Corrective Action Required.

### 5.2 Repeated Poor Performance

A supplier exceeding the review threshold for two consecutive quarters requires management review. For this rule, exceeding the review threshold means a quarterly Defect Rate greater than or equal to 2.00%. The two periods must be consecutive calendar or approved fiscal quarters and must use the same KPI calculation basis.

### 5.3 Severity Override

Major deviations must be escalated regardless of the supplier's overall quarterly defect rate. A supplier at 1.50% with a confirmed major deviation is not handled solely as Acceptable; the deviation requires escalation under POL-SQ-007 and QP-SQ-012.

## 6. Decision Rules

1. Confirm the supplier, site, material scope, and reporting period.
2. Calculate Inspected Count and Defect Count according to KPI-SQ-002.
3. Calculate Defect Rate only when Inspected Count is greater than zero.
4. Apply the exact classification boundaries in section 5.1.
5. Check the previous quarter for the consecutive-quarter rule.
6. Check deviation severity and repeated nonconformance independently of the aggregate rate.
7. Record the classification, evidence references, reviewer, decision date, and required follow-up.

If Inspected Count is zero, Defect Rate is not calculable. It shall not be reported as 0.00% and shall not be classified solely through the threshold table.

## 7. Exceptions

Quality Management may approve a documented temporary deviation from routine monitoring frequency when objective evidence supports the change. No exception may waive immediate escalation for a critical nonconformance, remove the major-deviation override, redefine the KPI formula, or change the 2.00% and 5.00% boundaries without controlled revision of this manual and related documents.

## 8. Management Review and Escalation

Management review may examine supplier performance, inspection history, open quality issues, containment status, corrective action status, delivery or production exposure, and future sourcing risk. Escalation levels, timing, owners, and exit criteria are defined in QP-SQ-012. Nonconformance severity is defined in POL-SQ-007.

## 9. Records and Evidence

The decision record shall identify the supplier, reporting period, applicable inspections, Inspected Count, Defect Count, Defect Rate, deviations, classification, escalation level, and approver. Records shall be retained for seven years unless a legal, customer, or product-specific schedule requires longer retention. Full private document content shall not be copied into operational logs.

## 10. Related Documents

- KPI-SQ-002, Supplier Quality KPI Definitions
- QP-INSP-004, Incoming Inspection Procedure
- POL-SQ-007, Supplier Nonconformance Policy
- QP-SQ-012, Quality Escalation Procedure

## 11. Revision History

| Version | Effective Date | Change Summary | Approver |
| --- | --- | --- | --- |
| 2.0 | 2025-04-01 | Consolidated supplier classification and escalation governance. | Director of Quality |
| 2.1 | 2026-01-01 | Clarified 2.00% and 5.00% boundaries, zero denominator, and major-deviation override. | Director of Quality |

End of controlled document SQM-001, version 2.1.

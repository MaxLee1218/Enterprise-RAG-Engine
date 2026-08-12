# Incoming Inspection Procedure

| Control Field | Value |
| --- | --- |
| Document ID | QP-INSP-004 |
| Document Type | Quality Procedure |
| Version | 1.6 |
| Effective Date | 2026-01-01 |
| Document Owner | Incoming Quality Engineering |
| Approved By | Quality Operations Manager |
| Classification | Internal |
| Business Function | Incoming Quality Control |
| Applicable Scope | Receipts requiring incoming inspection at approved manufacturing sites |

Controlled document. Printed copies are uncontrolled unless stamped and dated by Document Control. This synthetic document contains no real company confidential information.

## 1. Purpose

This procedure defines the controlled workflow for receiving, sampling, inspecting, accepting, rejecting, recording, and escalating incoming supplier material. It ensures that inspection quantities and outcomes support the authoritative Supplier Quality KPI definitions.

## 2. Scope

The procedure applies to incoming materials, production components, and critical components assigned an incoming inspection plan. It begins when a receipt is placed in inspection status and ends when the inspection record is completed, evidence is attached, and the disposition or escalation is recorded.

## 3. Definitions

| Term | Controlled Definition |
| --- | --- |
| Inspection Record | One database or controlled-system record representing an inspection event. It is not the Inspected Count. |
| total_quantity | Total number of individual units inspected for the inspection record. |
| rejected_quantity | Number of inspected units that fail the applicable acceptance criteria. |
| accepted_quantity | total_quantity minus rejected_quantity after completion and reconciliation. |
| Inspected Quantity | Total number of individual units inspected; for analytics this equals SUM(total_quantity). |
| Rejected Quantity | Number of inspected units failing acceptance criteria; for analytics this equals SUM(rejected_quantity). |
| Sampling Plan | Approved rule that specifies the units selected and acceptance criteria for a lot. |

## 4. Roles and Responsibilities

1. Receiving identifies the supplier, purchase order, item, lot, received quantity, and receipt date.
2. Incoming Inspector follows the approved sampling plan, records unit quantities, and preserves objective evidence.
3. Quality Engineer evaluates nonconformance severity and determines whether escalation is required.
4. Material Review authority approves disposition where required; this procedure does not grant automated systems disposition authority.
5. Supplier Quality uses completed records for supplier performance analysis under KPI-SQ-002 and SQM-001.

## 5. Procedure

### 5.1 Receipt and Identification

1. Verify that the supplier is approved for the item and site.
2. Record supplier_id, item identifier, lot or batch, receipt identifier, and inspection period.
3. Place material in controlled inspection status so it cannot be released before disposition.
4. Select the approved inspection plan based on item criticality, supplier status, and current revision.

### 5.2 Sampling and Inspection

1. Select units without substituting a record count for a unit count.
2. Perform specified dimensional, visual, functional, documentation, or material tests.
3. Record each observed failure against the applicable criterion.
4. Preserve measurement results, certificates, images, and deviation references as required.

### 5.3 Quantity Reconciliation

The completed inspection record shall satisfy all of the following controls:

- total_quantity is a non-negative integer representing individual inspected units.
- rejected_quantity is a non-negative integer representing failed inspected units.
- rejected_quantity shall not exceed total_quantity.
- accepted_quantity equals total_quantity minus rejected_quantity.
- The inspection record count shall never be used as Inspected Count.

Example: one inspection record has total_quantity = 1,000 and rejected_quantity = 30. Inspected Quantity is 1,000 units, Rejected Quantity is 30 units, and Defect Rate is 30 / 1,000 = 3.00%. The result is not 1 / 30 and is not based on one inspection record.

### 5.4 Result and Disposition

| Result | Minimum Required Record |
| --- | --- |
| Accepted | Completed quantities, acceptance evidence, inspector, date, and release reference |
| Rejected | Completed quantities, failed criteria, containment location, nonconformance reference, and disposition status |
| Conditional or Deviation | Approved deviation reference, scope, expiry, authorized approver, and affected quantity |

An inspection is complete only when required tests are finished, quantities reconcile, evidence is attached or referenced, and the responsible inspector records completion. A partially completed record shall not be included as a completed inspection unless the analytics contract explicitly selects it.

## 6. Decision Rules

1. Calculate period Inspected Count as SUM(total_quantity) for all applicable completed incoming inspection records.
2. Calculate period Defect Count as SUM(rejected_quantity) for the same applicable record set.
3. Calculate Defect Rate as Defect Count divided by Inspected Count according to KPI-SQ-002.
4. If Inspected Count is zero, report the rate as not calculable, not 0.00%.
5. Apply supplier classification according to SQM-001 only after confirming the period and data scope.
6. Apply severity rules independently of the aggregate Defect Rate.

## 7. Exceptions

Reduced inspection, skip-lot, dock-to-stock, source inspection, or customer-directed inspection may be used only when an approved plan identifies the authorization and effective period. Such an exception does not change the meanings of total_quantity or rejected_quantity and does not waive escalation for major or critical nonconformance.

## 8. Escalation

Escalation requirements are defined in QP-SQ-012. A major deviation shall be escalated regardless of aggregate quarterly defect rate. A critical safety, regulatory, or counterfeit concern requires immediate containment and escalation under POL-SQ-007. Inspectors shall not wait for end-of-quarter KPI calculation before reporting a severity event.

## 9. Records and Evidence

Required evidence includes the receipt record, inspection plan revision, inspection results, total_quantity, rejected_quantity, accepted_quantity, inspector identity, completion timestamp, nonconformance reference, material status, and disposition approval when applicable. Records shall be retained for seven years unless a longer requirement applies.

## 10. Related Documents

- SQM-001, Supplier Quality Manual
- KPI-SQ-002, Supplier Quality KPI Definitions
- POL-SQ-007, Supplier Nonconformance Policy
- QP-SQ-012, Quality Escalation Procedure

## 11. Revision History

| Version | Effective Date | Change Summary | Approver |
| --- | --- | --- | --- |
| 1.5 | 2025-05-01 | Added quantity reconciliation and completion controls. | Quality Operations Manager |
| 1.6 | 2026-01-01 | Aligned inspected and rejected quantities with KPI-SQ-002 and clarified escalation timing. | Quality Operations Manager |

End of controlled document QP-INSP-004, version 1.6.

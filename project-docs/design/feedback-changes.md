\# Design changes after formative feedback (\[02/12/2026])



\## Feedback received

1\. The feature should be clearly named "toxicity detection".

2\. Requirements were good (no change).

3\. Only four diagrams are needed: use case, class, architecture and activity.

4\. Use case diagram: the Administrator was not connected to "Create report" and "Score toxicity".

5\. Class diagram: show the content of each class, not only what type of class it is.



\## Changes made

| Diagram | Version | Change |

|---|---|---|

| Use case | v1 -> v2 | Administrator connected directly to "Detect post toxicity" and "Create toxicity report"; use cases renamed to toxicity detection; extend condition \[score >= threshold] added; key added |

| Class | v1 -> v2 | Post, Report and User now show their real attributes and methods from FlaskBB; type tags removed; classes renamed (ToxicityDetectionService, ToxicityResult, ToxicityScore); multiplicities and role names added |

| Architecture | new | Replaces the component diagram: layered view of FlaskBB with PostgreSQL and the Toxicity Detection plugin connected through pluggy |

| Activity | v1 -> v2 | Swimlanes (Member, FlaskBB, plugin, Moderator); fork for parallel flows; notes for fail-open and human decision |

| Sequence | dropped | Not required by the tutor; kept in v1 for reference |



v1 files are kept unchanged as evidence of iteration.


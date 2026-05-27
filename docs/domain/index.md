# Domain Knowledge Guide

> Explains the background knowledge developers without a robotics background need to understand this project.

## Where this project fits

OpenLUTRA is a tool for recording **teaching data** (demonstration motions) from a robot. The recorded MCAP files are processed into imitation-learning data for AI by a separate conversion/annotation pipeline.

```
[Physical robot] ──ROS2──▶ [OpenLUTRA (this repo)] ──▶ [MCAP file]
                                                          │
                                                          ▼
                                            External conversion/annotation
                                            pipeline (LeRobot, etc.)
```

This repository's scope ends at **MCAP recording and quality verification**. It does not handle downstream conversion or upload.

## Domain knowledge

| Document | Contents |
|---|---|
| [DDS communication and gaps](dds_gap.md) | Why messages get lost over DDS, how it relates to QoS, and how to tune it |
| [Quality analysis](quality_analysis.md) | Metrics, score calculation, status determination |
| [Custom validators](custom_validators.md) | How the per-recording auto-validation works, and how to add your own rules |
| [SSE stream](sse.md) | Spec for real-time data delivery (event list, connection example) |

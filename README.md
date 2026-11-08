# Frontline DX Pilot Tracker

A web system that supports how a digital transformation (DX) team actually works:
listen to frontline employees, understand the workflow, set an improvement goal, run a
small-scale pilot, measure whether it worked, and share what was learned across
businesses.

> **Status: in development (started November 2026).** The Status columns show what is
> built and what is planned. All data is synthetic and the system is a pilot to show an
> approach. It does not use any real company data.

## The problem

A DX team supporting several businesses (railways, buses, amusement parks, hotels,
restaurants, retail and real estate) hears about problems in conversations, emails and
spreadsheets. As a result:

- Problems get lost, or are fixed twice by different people.
- It is unclear which problem to solve first.
- Pilots start without a clear goal or metric, so nobody can say afterwards whether they
  worked.
- A lesson from one business (say, automating a daily sales report in a hotel) never
  reaches another (say, a retail shop with the same reporting pain).
- Nobody can show the benefit of DX work in numbers: hours saved, errors avoided, reports
  delivered earlier.

## What it does

The tracker follows one problem from first report to measured result:

1. **Listen:** frontline staff report a problem, or a planner records one after an
   interview with them.
2. **Understand the workflow:** the report captures the current steps, who is involved,
   how often it happens and how long it takes.
3. **Set the goal:** a planner defines the improvement goal and the metric that will judge
   it, before any work starts.
4. **Pilot on a small scale:** the pilot is limited to one team or site, with a start and
   end date and an owner.
5. **Measure effectiveness:** results are recorded before and after, with how each number
   was measured.
6. **Adopt or stop:** a manager decides to roll out, adjust or stop, and the reason is kept.
7. **Reuse:** finished pilots go into a searchable library for other businesses.

## Features

| Feature | Status |
|---|---|
| Problem report form: business, area, current workflow, frequency, minutes per occurrence, people affected | Planned |
| Request and incident categories with status tracking (new, triaged, in pilot, resolved) | Planned |
| Priority score from frequency, time lost and people affected (a simple, explainable rule) | Planned |
| Pilot plan: goal, metric, baseline, target, scope, timeline, owner | Planned |
| Rule that a pilot cannot start without a metric and a baseline | Planned |
| Before-and-after results with the measurement method recorded | Planned |
| Effectiveness calculation: hours saved per month and percentage improvement | Planned |
| Approval flow with stakeholders: draft, review, approved, running, finished | Planned |
| Comments and decisions on each problem and pilot | Planned |
| Roles and access control, enforced on the server | Planned |
| Audit log of who changed what and when | Planned |
| Analytics dashboard (SQL views): problems by business, pilots by status, hours saved | Planned |
| Weekly summary report generated automatically as PDF or Excel | Planned |
| Searchable library of finished pilots | Planned |
| Draft categorisation suggestions from the problem text, always confirmed by a person | Planned (stretch) |
| Sample scenarios in synthetic data (see below) | Planned |

## Sample scenarios

These are synthetic examples used to test the system, based on the kinds of challenges a
multi-business group has:

| Business | Problem | Pilot idea |
|---|---|---|
| Railways and buses | Passenger usage data is collected by hand, and reporting is slow | Automate data collection and a weekly usage report |
| Amusement park | Visitor data is not used to improve customer service | A dashboard of visitor numbers and waiting times |
| Hotels, restaurants, retail | Reservation and sales reports take staff an hour each day | Automate the daily report; measure minutes saved and errors found |
| Real estate | Contract and property information is spread across files | Organise contract expiry dates in one place, with reminders |

## How effectiveness is measured

A pilot is judged on a number agreed before it starts.

- **Baseline:** the measured value before the change, with the method used (for example,
  timing a report being prepared on five different days).
- **Result:** the same measurement after the change.
- **Hours saved per month** = (minutes before − minutes after) × occurrences per month ÷ 60.
- **Improvement** = (before − after) ÷ before, shown as a percentage.
- Quality measures (errors found, reports delivered late) are recorded the same way.
- The decision to adopt, adjust or stop is stored with the reason.

## Users and roles

| Role | What they can do |
|---|---|
| **Frontline staff** | Report problems and follow the status of their own reports |
| **DX planner** | Triage reports, define pilots, record results |
| **Manager** | Approve pilots and decide on roll-out for the businesses they cover |
| **External vendor** (limited) | See only the pilots assigned to them, with no other business data |
| **Admin** | Manage users and roles, read the audit log |

## Information security

- Passwords are hashed and never stored in plain text.
- Permissions are checked on the server for every action, with deny as the default.
- Each role sees only the businesses and pilots it is linked to in the database.
- Input is validated on every form, and queries are parameterised.
- Secrets are read from environment variables, not from code.
- Every change is written to an audit log with the user and the time.
- Automated tests check these rules, for example that a user cannot open another
  business's problem by changing a URL.

## Planned data model

| Table | Purpose |
|---|---|
| `users`, `roles`, `user_businesses` | Logins with hashed passwords, roles, and which businesses each user may see |
| `businesses` | The businesses the team serves |
| `problems` | A reported problem: business, area, workflow, frequency, minutes lost, status |
| `pilots` | A pilot linked to a problem: goal, metric, baseline, target, scope, dates, owner, status |
| `pilot_results` | Before and after values and how they were measured |
| `decisions` | Adopt, adjust or stop, with the reason and who decided |
| `comments` | Discussion on a problem or pilot |
| `audit_log` | Every change, with the user and the time |

## How it is being built (development lifecycle)

| Stage | Status |
|---|---|
| Requirements: users, user stories, scope, success measures | Next |
| Design: data model, roles and permissions, screens | Planned |
| Implementation in small steps, one feature at a time | Planned |
| Testing: automated tests for permissions, workflow rules and calculations | Planned |
| Deployment on AWS (virtual server and managed database) | Planned |
| Evaluation: run a sample pilot end to end and record the effect | Planned |

## Tech

Python 3.11, Django, PostgreSQL and SQL for the analytics views, pytest for testing, Git
and GitHub for version control, AWS for deployment.

## Limitations

- Synthetic data only, so the numbers show how the system works, not real savings.
- The priority score starts as a transparent rule, not a machine-learning model.
- Any AI suggestion is a draft that a person must confirm.

## Documents

- Requirements: coming first
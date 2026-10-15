# TrackIt — Use Case Specification

> Provisional application name: **TrackIt**
> Status: requirements analysis only. No implementation decisions are made here.
> This document defines *expected system behavior*; it deliberately does not choose
> database, API, authentication mechanism, framework, architecture, or file layout.

---

## 1. Purpose and scope

TrackIt lets **registered users** manage **personal projects** and the **tasks**
inside those projects. Every project belongs to exactly one user; every task
belongs to exactly one project. Users are fully isolated: no user may see or
change another user's data.

**In scope (from the requirements):**
- Account registration, login, logout.
- Full lifecycle of projects (list, create, read, update, delete).
- Full lifecycle of tasks inside a project (list, create, read, update, delete,
  plus marking complete/pending).
- Ownership-based isolation and the behavioral rules for unauthorized access.

**Out of scope at this stage:** anything not stated in the requirements
(see §9). Candidate additions that the requirements do *not* currently cover are
listed explicitly in §7 so they can be accepted or rejected before design.

---

## 2. Actors

| Actor | Description |
|---|---|
| **Visitor** | An unauthenticated person. May reach public screens (register, login) only. |
| **User** | An authenticated person. Owns zero or more projects. |
| **Owner** | A User acting on a resource (project or task) that belongs to them. Not a separate kind of account — it is the relationship of a User to a specific resource. |
| **Non-owner** | A User acting on a resource that exists but belongs to someone else. |

There is no administrator, team, or sharing role in the current requirements.

---

## 3. Domain model (conceptual, not a schema)

- **User** — identified by a unique email address; authenticates with a password.
  Owns projects.
- **Project** — belongs to exactly one User (its Owner). Has a name/title (and
  possibly a description; see §8). Contains tasks.
- **Task** — belongs to exactly one Project. Has a title/description and a
  completion state of exactly one of: **pending** or **completed**.

Ownership is transitive: a task is effectively owned by the owner of its project.

---

## 4. Authorization states (cross-cutting)

The system must distinguish three states; the expected reaction per resource type
is normative.

| State | Request target | Expected behavior |
|---|---|---|
| **Unauthenticated** | Public screen (register, login) | Allowed. |
| **Unauthenticated** | Any protected screen / any project or task | Not allowed. Redirect to login (no data shown, no write performed). |
| **Authenticated** | Own resource | Allowed. |
| **Authenticated** | Nonexistent resource | "Not found" response. |
| **Authenticated** | Existing resource owned by another user | Denied. Whether it is reported as "forbidden" or disguised as "not found" **must be decided** (see §8). Default recommendation: respond as "not found" so resource existence is not leaked. |

Authorization is checked for **read and write** actions equally, on every
project and task operation, including nested task operations (through the
project's owner).

---

## 5. Use case catalog

Areas:
- **A — Account & authentication**
- **B — Projects**
- **C — Tasks**
- **D — Access control (cross-cutting behaviors)**

Legend: preconditions assume the actor is a Visitor unless stated otherwise.

---

### Functional area A — Account & authentication

#### UC-A1 — Register account
- **Actor:** Visitor
- **Preconditions:** No active session (or session treated as guest).
- **Main flow:**
  1. Visitor submits registration data: email address and password.
  2. System validates the data (required, email format, password rules).
  3. System confirms the email is not already registered.
  4. System creates the account and authenticates the new user (or, if the
     product prefers, sends the user to login — this is a decision; see §8).
- **Expected outcome:** A new User exists and is the only owner of their future
  projects. Behavior is identical for the first and subsequent registrations.
- **Errors / alternatives:**
  - **E1 Duplicate email:** registration is rejected; no account is created.
    Whether the message says "email already in use" explicitly or a generic
    message is a decision (§8).
  - **E2 Invalid data:** missing/invalid email, password failing policy, or
    (if present) mismatched password confirmation. Registration is rejected,
    fields are re-shown with errors, nothing is persisted.
  - **E3 Malformed/oversized input:** rejected by the same validation rules.

#### UC-A2 — Log in
- **Actor:** Visitor (with an existing account)
- **Preconditions:** An account exists for the supplied email.
- **Main flow:**
  1. Visitor submits email and password.
  2. System verifies the credentials.
  3. System starts an authenticated session.
  4. System routes the user to their projects.
- **Expected outcome:** The session is authenticated; the user can act as Owner
  of their own data.
- **Errors / alternatives:**
  - **E1 Incorrect credentials:** authentication fails. Error message must be
    generic ("email or password is incorrect") and must not reveal whether the
    email exists. No session is created.
  - **E2 Missing fields:** form shown again with validation errors.
  - **E3 Already authenticated:** decide whether visiting login redirects to the
    projects screen (§8).

#### UC-A3 — Log out
- **Actor:** User
- **Preconditions:** Authenticated session.
- **Main flow:** User requests logout → system ends the session.
- **Expected outcome:** No authenticated session remains. Protected screens and
  resources are no longer reachable, including via browser "back" to a cached
  view (at minimum, the server must reject the next request).
- **Errors / alternatives:**
  - **E1 Logout while unauthenticated:** treat as a no-op and send to login
    (must not error).
  - **E2 Session already expired:** same as E1.

#### UC-A4 — View own account *(missing requirement — see §7)*
- **Actor:** User
- **Main flow:** User views their own profile/identity (at least the email the
  account was created with).
- **Expected outcome:** The user can confirm who they are logged in as.
- **Notes:** Needed for even a minimal account experience and for a logout
  affordance; not present in the stated requirements.

#### UC-A5 — Handle expired/invalid session *(missing requirement — see §7)*
- **Actor:** User with a stale session, or Visitor
- **Main flow:** Any request carrying an expired or invalid session is treated as
  unauthenticated (→ redirect to login) rather than producing a server error.
- **Notes:** Necessity depends on whether sessions expire (a decision, §8), but
  the *behavior* must be defined either way.

---

### Functional area B — Projects

#### UC-B1 — List own projects
- **Actor:** User
- **Preconditions:** Authenticated.
- **Main flow:** User opens the projects screen → system returns **only** the
  projects owned by that user.
- **Expected outcome:** The list contains the user's projects and nothing from
  other users. If the user has none, an empty state is shown.
- **Errors / alternatives:**
  - **E1 Unauthenticated:** redirect to login (UC-D1).
  - **E2 No projects:** empty state with a call to create one; not an error.
- **Notes:** Ordering (e.g., by creation date or name) is a decision (§8).

#### UC-B2 — Create project
- **Actor:** User
- **Preconditions:** Authenticated.
- **Main flow:**
  1. User submits project data (at minimum a name/title).
  2. System validates the data.
  3. System creates the project with the current user as Owner.
- **Expected outcome:** A new project exists, owned by the current user, and
  becomes visible in their project list.
- **Errors / alternatives:**
  - **E1 Missing/invalid required data:** project is not created; form is
    re-shown with errors.
  - **E2 Unauthenticated:** redirect to login; nothing is created.
  - **E3 Duplicate project names:** duplicates are allowed by default (no rule
    forbids them) unless decided otherwise (§8).

#### UC-B3 — View project details
- **Actor:** User who is the Owner
- **Preconditions:** Authenticated; the project exists and is owned by the actor.
- **Main flow:** User opens a project → system returns the project's details,
  and (per requirements) the project's tasks.
- **Expected outcome:** The Owner sees their project and its tasks.
- **Errors / alternatives:**
  - **E1 Unauthenticated:** redirect to login (UC-D1).
  - **E2 Project does not exist:** "not found" (UC-D3).
  - **E3 Project exists but belongs to another user:** denied (UC-D2).
  - **Note:** whether the task list is part of this screen or a separate screen
    is a presentation decision; the *authorization* result must be identical.

#### UC-B4 — Update project
- **Actor:** User who is the Owner
- **Preconditions:** Authenticated; the project exists and is owned by the actor.
- **Main flow:**
  1. User submits changes to the project.
  2. System validates the data.
  3. System persists the changes.
- **Expected outcome:** The project reflects the new data; tasks are unaffected.
- **Errors / alternatives:**
  - **E1 Invalid data:** no change is persisted; errors are shown.
  - **E2 Project does not exist:** "not found" (UC-D3).
  - **E3 Not the Owner:** denied (UC-D2).
  - **E4 Unauthenticated:** redirect to login (UC-D1).

#### UC-B5 — Delete project
- **Actor:** User who is the Owner
- **Preconditions:** Authenticated; the project exists and is owned by the actor.
- **Main flow:** User requests deletion → system deletes the project.
- **Expected outcome:** The project is gone from the Owner's list and is no longer
  reachable.
- **Errors / alternatives:**
  - **E1 Project does not exist:** "not found" (UC-D3).
  - **E2 Not the Owner:** denied (UC-D2); nothing is deleted.
  - **E3 Unauthenticated:** redirect to login (UC-D1).
  - **E4 Open question — contained tasks:** what happens to the project's tasks?
    Cascade-delete them, or block deletion? **Must be decided** (§8). This is the
    single most consequential unresolved rule in the project lifecycle.
  - **E5 Confirmation:** whether the UI requires an explicit confirmation step
    before deleting is a presentation decision (§8).

---

### Functional area C — Tasks

Tasks are always accessed **within the context of a project**. Every task use case
therefore re-checks that the actor owns the parent project.

#### UC-C1 — List tasks of a project
- **Actor:** Owner of the parent project
- **Preconditions:** Authenticated; project exists and is owned by the actor.
- **Main flow:** User opens a project's task list → system returns that project's
  tasks only.
- **Expected outcome:** Only tasks belonging to the specified project are shown;
  tasks from other projects or other users are never included.
- **Errors / alternatives:**
  - **E1 Project missing:** "not found" (UC-D3).
  - **E2 Not the Owner:** denied (UC-D2).
  - **E3 Unauthenticated:** redirect to login (UC-D1).
  - **E4 No tasks:** empty state; not an error.

#### UC-C2 — Create task in a project
- **Actor:** Owner of the parent project
- **Preconditions:** Authenticated; project exists and is owned by the actor.
- **Main flow:**
  1. User submits task data (at minimum a title; see §8 for required fields).
  2. System validates the data.
  3. System creates the task belonging to that project.
- **Expected outcome:** A new task exists inside the project; its initial state is
  **pending** (default — confirm in §8).
- **Errors / alternatives:**
  - **E1 Missing required data:** task is not created; form re-shown with errors.
    (Directly required by the brief.)
  - **E2 Parent project does not exist:** "not found" (UC-D3).
  - **E3 Not the Owner of the parent project:** denied (UC-D2); nothing created.
  - **E4 Unauthenticated:** redirect to login (UC-D1).
  - **E5 Client-supplied project ownership:** any attempt to attach the task to a
    project the user does not own must be rejected (UC-D2).

#### UC-C3 — View task details
- **Actor:** Owner of the parent project
- **Preconditions:** Authenticated; task exists; its project is owned by the actor.
- **Main flow:** User opens a task → system returns its details.
- **Expected outcome:** Task details are shown.
- **Errors / alternatives:**
  - **E1 Task does not exist:** "not found" (UC-D3).
  - **E2 Task exists but its project belongs to another user:** denied (UC-D2).
  - **E3 Unauthenticated:** redirect to login (UC-D1).

#### UC-C4 — Update task
- **Actor:** Owner of the parent project
- **Preconditions:** Authenticated; task exists; its project is owned by the actor.
- **Main flow:** User submits changes → system validates → system persists them.
- **Expected outcome:** The task reflects the new data.
- **Errors / alternatives:**
  - **E1 Invalid data:** no change persisted; errors shown.
  - **E2 Task does not exist:** "not found" (UC-D3).
  - **E3 Not the Owner (directly or via the project):** denied (UC-D2).
  - **E4 Unauthenticated:** redirect to login (UC-D1).
  - **E5 Reassigning the task to another project:** unless explicitly supported,
    the task's project must be immutable via update (see §7/§8).

#### UC-C5 — Mark task completed / pending
- **Actor:** Owner of the parent project
- **Preconditions:** Authenticated; task exists; its project is owned by the actor.
- **Main flow:**
  1. User toggles (or sets) the task's completion state.
  2. System persists the new state: **completed** or **pending**.
- **Expected outcome:** The task's completion state changes accordingly and is
  reflected in the list.
- **Errors / alternatives:**
  - **E1 Task does not exist:** "not found" (UC-D3).
  - **E2 Not the Owner:** denied (UC-D2).
  - **E3 Unauthenticated:** redirect to login (UC-D1).
  - **E4 Idempotency:** marking an already-completed task completed again leaves
    it completed without error (and vice versa).
- **Notes:** This is treated as its own use case because the requirements call it
  out separately; it may also be a special case of UC-C4 (see §8).

#### UC-C6 — Delete task
- **Actor:** Owner of the parent project
- **Preconditions:** Authenticated; task exists; its project is owned by the actor.
- **Main flow:** User requests deletion → system deletes the task.
- **Expected outcome:** The task is removed from the project; the project remains.
- **Errors / alternatives:**
  - **E1 Task does not exist:** "not found" (UC-D3).
  - **E2 Not the Owner:** denied (UC-D2); nothing deleted.
  - **E3 Unauthenticated:** redirect to login (UC-D1).
  - **E4 Confirmation step:** presentation decision (§8).

---

### Functional area D — Access control (cross-cutting behaviors)

These are behavioral use cases triggered as alternative flows of the ones above.
They are listed separately because the brief explicitly requires the system to
distinguish the three states.

#### UC-D1 — Reject unauthenticated access to a protected resource
- **Actor:** Visitor
- **Preconditions:** No valid session.
- **Trigger:** Request for any protected screen, project, or task.
- **Main flow:** System does not reveal or modify any data; sends the user to the
  login screen.
- **Expected outcome:** No protected data is disclosed and no write occurs.
- **Alternatives / decisions:**
  - Whether the originally requested destination is remembered and restored after
    login is a decision (§8).
  - Whether the response is a redirect (browser) or an "unauthorized" status
    (API) is an implementation detail; the *behavior* — deny and require login —
    is fixed here.

#### UC-D2 — Reject access to a resource owned by another user
- **Actor:** Authenticated Non-owner
- **Preconditions:** Session is valid; the target resource exists and belongs to a
  different user.
- **Trigger:** Any read or write attempt on that project or task, including via a
  directly typed URL/identifier.
- **Main flow:** System denies the request; no data is returned and no change is
  made.
- **Expected outcome:** The other user's data remains confidential and unmodified.
- **Decisions:** Whether the response is "forbidden" or indistinguishable from
  "not found" must be chosen (§8). Recommendation: make it indistinguishable from
  not-found so the existence of the resource is not leaked. Either way, the
  system must **never** fall back to treating the resource as the actor's own.

#### UC-D3 — Reject access to a nonexistent resource
- **Actor:** User (or Visitor)
- **Preconditions:** The requested project or task identifier does not exist.
- **Main flow:** System returns a "not found" result.
- **Expected outcome:** No data is returned, no record is created as a side effect,
  and no server error is surfaced.
- **Notes:** Applies uniformly to view, update, toggle, and delete.

---

## 6. Requirement traceability

| Behavioral requirement from the brief | Covered by |
|---|---|
| Register with an already-existing email | UC-A1 / E1 |
| Invalid registration data | UC-A1 / E2, E3 |
| Login with incorrect credentials | UC-A2 / E1 |
| Access a protected page while not logged in | UC-D1 |
| Access a project that does not exist | UC-D3 (via UC-B3) |
| Access a project that exists but belongs to another user | UC-D2 (via UC-B3) |
| Create a task without required data | UC-C2 / E1 |
| Update or delete a resource that does not exist | UC-D3 (via UC-B4, B5, C4, C5, C6) |
| Distinguish unauthenticated / authenticated / non-owner | UC-D1, UC-D2, UC-D3 + §4 |

---

## 7. Potentially missing use cases

These are **not** in the requirements as written. They are flagged because the
system is likely to be incomplete, insecure, or unusable without at least a
decision on each. They are proposals, not additions to scope.

1. **View own account (UC-A4).** Without it, a user cannot confirm which account
   is active, and the UI has no natural home for the logout action. Low cost.
2. **Session expiry / invalid-session handling (UC-A5).** "Log out" is specified,
   but nothing says whether sessions ever expire. If they do, the behavior on
   expiry must be defined (treat as unauthenticated) to avoid crashes.
3. **Change password / forgot password.** Real accounts need a recovery path.
   This is arguably outside the stated scope, but its *absence* means a user who
   forgets their password is permanently locked out. Decide in/out explicitly.
4. **Email verification.** If registration must guarantee the email belongs to the
   user, a verification step is needed. Otherwise, say clearly that it is not
   required.
5. **Move/reassign a task to another project.** The model says a task belongs to
   exactly one project, which is satisfied by making the project immutable.
   If users are expected to reorganize, this is a distinct use case; if not,
   explicitly state that a task's project cannot change.
6. **Filtering, sorting, or searching tasks/projects.** Not required, but the
   project list and a project's task list will become hard to use as data grows.
   Also relates to whether lists are paginated.
7. **Cascade/impact of project deletion on tasks.** Not a new use case, but an
   essential rule (see UC-B5/E4). It determines data integrity.
8. **Concurrent edits.** Two sessions editing the same project/task. The
   requirements say nothing; default "last write wins" is fine, but should be an
   explicit non-goal or rule.
9. **Delete/close account.** Out of scope unless stated; flagging only so the
   omission is intentional.
10. **Rate limiting / brute-force protection on login and registration.** A
    security expectation rather than a user-facing use case; decide whether it is
    in scope (authentication *mechanism* is explicitly deferred, but this is
    behavior, not mechanism).

---

## 8. Ambiguities and contradictions to resolve before implementation

1. **403 vs 404 for another user's resource (UC-D2).** Security best practice
   favors making it indistinguishable from "not found". The brief says the system
   must *distinguish* the non-owner case internally, which is compatible with
   returning 404 externally — but this must be confirmed.
2. **Project deletion and its tasks (UC-B5/E4).** Delete tasks with the project,
   or refuse to delete a non-empty project? Contradiction risk: an "orphan" task
   is impossible if tasks belong to exactly one project, so cascade-delete is the
   natural reading — confirm.
3. **Duplicate-email message (UC-A1/E1).** Say "email already registered"
   (better UX, leaks account existence) or use a generic message (better privacy).
4. **Post-registration state (UC-A1).** Auto-login after registration, or redirect
   to login? Both are reasonable; pick one.
5. **Required fields.** The brief names no fields. At minimum a project name and a
   task title should be required, but this must be stated, along with optional
   fields (project description? task description?).
6. **Password policy.** Minimum length/complexity — undefined. Also whether a
   password confirmation field exists.
7. **Email normalization.** Are `User@x.com` and `user@x.com` the same account
   (case-insensitive uniqueness)? Is input trimmed? This affects the duplicate-email
   rule.
8. **Task status: boolean vs. richer states.** The brief uses "mark as completed or
   pending", which implies a two-value state, yet calls the field a *status*. A
   two-value state is the safer scope reading; confirm that no intermediate
   states (e.g., "in progress") are expected.
9. **Is "mark complete" a special case of "update"? (UC-C5 vs UC-C4).** If it is a
   normal field update, UC-C5 need not exist separately in the API; the behavior
   still must be specified.
10. **Default task state on creation.** Presumed **pending**; confirm.
11. **Ordering of lists.** Default ordering for the project list and task list
    (creation date, name, status) is undefined.
12. **Restore destination after login (UC-D1).** After being redirected to login,
    should the user land on the page they originally requested, or on the general
    projects list?
13. **Visiting login/register while already authenticated (UC-A2/E3).** Redirect
    to the projects list, or show the page?
14. **Session lifetime and "remember me".** Undefined; interacts with UC-A5.
15. **Scope of a global task view.** The brief only defines tasks *within a
    project*. Confirm there is no cross-project "all my tasks" screen, so it is not
    designed later by accident.
16. **Deletion confirmation and soft vs. hard delete.** Presentation-level, but the
    underlying rule (irreversible delete?) should be explicit.
17. **Data limits.** Maximum lengths for names/descriptions and maximum counts are
    undefined; relevant to validation rules and to rendering.
18. **Terminology.** The repo directory is `TrackTear` while the product is
    `TrackIt` — clarify the final name to avoid confusion in later docs.

---

## 9. Out of scope (explicit non-goals)

Unless separately requested, the following are **not** part of TrackIt as specified:

- Sharing, collaboration, teams, or assigning tasks to other users.
- Roles/permissions beyond "owner of my own data".
- Administrators or any account that can see other users' data.
- Subtasks, dependencies, comments, attachments, tags, labels.
- Notifications, reminders, due dates, priorities, recurring tasks.
- Public or anonymous access to any project or task.
- Integrations, imports/exports, reporting, or analytics.
- Any choice of framework, database, hosting, auth mechanism, or file layout.

---

## 10. Summary of use cases

| ID | Use case | Actor |
|---|---|---|
| UC-A1 | Register account | Visitor |
| UC-A2 | Log in | Visitor |
| UC-A3 | Log out | User |
| UC-A4 | View own account *(proposed)* | User |
| UC-A5 | Handle expired/invalid session *(proposed)* | User / Visitor |
| UC-B1 | List own projects | User |
| UC-B2 | Create project | User |
| UC-B3 | View project details | Owner |
| UC-B4 | Update project | Owner |
| UC-B5 | Delete project | Owner |
| UC-C1 | List tasks of a project | Owner |
| UC-C2 | Create task in a project | Owner |
| UC-C3 | View task details | Owner |
| UC-C4 | Update task | Owner |
| UC-C5 | Mark task completed / pending | Owner |
| UC-C6 | Delete task | Owner |
| UC-D1 | Reject unauthenticated access | Visitor |
| UC-D2 | Reject access to another user's resource | Non-owner |
| UC-D3 | Reject access to a nonexistent resource | User / Visitor |

**Core (required):** UC-A1, UC-A2, UC-A3, UC-B1 through UC-B5, UC-C1 through UC-C6,
UC-D1 through UC-D3.
**Proposed additions pending approval:** UC-A4, UC-A5 (plus the §7 items).

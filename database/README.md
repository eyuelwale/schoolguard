# SchoolGuard MySQL

The schema is designed around these domains:

1. users / authentication
2. schools
3. classes
4. students
5. parent-child relationships
6. teacher-class assignments
7. attendance records
8. attendance events
9. schedules
10. notification preferences
11. notifications/outbox
12. registration/link codes
13. audit logs

For a multi-school SaaS, keep `school_id` on every tenant-owned table and enforce it in every service query.

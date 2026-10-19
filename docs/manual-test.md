# Manual Test Guide

1. Open the app and register `test@example.com`.
2. Confirm the default categories exist.
3. Add three transactions in two different categories for the current month.
4. Open the dashboard and confirm the total and the category chart match what you entered.
5. Import a CSV with 5 valid rows and 2 invalid rows. Confirm "5 imported, 2 rejected" with reasons.
6. Add a yearly subscription for 120.00 and confirm its monthly equivalent is 10.00.
7. Add a monthly subscription renewing in 5 days and confirm it appears under "Upcoming renewals".
8. Cancel one subscription and confirm the subscription total drops.
9. Log out, register a second user, and confirm none of the first user's data is visible.
10. Restart the app and confirm the data is still there (persistence).

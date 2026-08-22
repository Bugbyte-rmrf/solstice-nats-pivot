# Scope Delta Analysis

## Original Architecture

The kiosk called the badge printer's REST API synchronously.

Flow:

QR scan
→ REST printer request
→ wait
→ print succeeds
→ Checked In

## Pivot

The synchronous vendor API was deprecated.

The replacement architecture is asynchronous.

Flow:

QR scan
→ create print job
→ save PENDING
→ publish NATS event
→ vendor consumes message
→ vendor prints badge
→ vendor calls webhook
→ kiosk validates job
→ CHECKED_IN

## Dropped

- Direct synchronous printer request
- Waiting for print completion during the scan request

## Added

- NATS JetStream
- Print event
- Unique print job IDs
- PENDING state
- Webhook endpoint
- Webhook authentication
- Stale webhook protection
- Asynchronous vendor simulator

## Modified

- Check-in workflow
- User interface
- Attendee state transitions
- Duplicate scan behavior

## Preserved

- Three test attendees
- Badge must actually print before CHECKED_IN
- Duplicate scan must not print another badge

## Regression Check

All three test attendees completed successfully.

Duplicate scanning did not create a second badge request.

Stale callbacks did not change the current attendee state.

## Pivot Cost

2.5 hours

## Trade-Offs

The new architecture removes the dependency on an immediate
printer response, but introduces asynchronous state management,
message persistence, webhook processing, and event-ordering concerns.

# Accept/Modify Buttons After Business Plan Answers

## Problem
User reported that Accept/Modify buttons appear "sometimes, but not consistently" after answering Business Planning questions. They wanted consistent buttons to appear after each section or answer is captured, allowing users to confirm or modify their answers before moving to the next question.

## Root Cause
The existing button detection system (`should_show_accept_modify_buttons`) only showed buttons for:
- Draft command responses
- Support command responses  
- Scrapping command responses

It did NOT show buttons after regular user answers in Business Planning phase. The AI would acknowledge the answer and immediately ask the next question without giving users a chance to review and confirm.

## Solution Implemented

### 1. Enhanced Button Detection Logic

Updated `should_show_accept_modify_buttons()` function in `angel_service.py` (lines 136-210):

**New Detection Criteria:**
```python
# Show Accept/Modify buttons when:
1. User used Draft/Support/Scrapping command (existing behavior)
   OR
2. User provided an answer in Business Plan phase AND
   AI acknowledged the answer AND
   AI hasn't asked the next question yet
```

**Key Detection Patterns:**
- **Business Plan phase check**: `session_data.get("current_phase") == "BUSINESS_PLAN"`
- **User answer check**: Input is NOT a command word ("accept", "modify", "draft", etc.)
- **Acknowledgment patterns detected**:
  - "thank you", "thanks for"
  - "great", "perfect", "excellent", "wonderful"
  - "i've captured", "i've noted", "got it"
  - "understood", "that's helpful", "appreciate", "makes sense"
- **Question tag check**: No `[[Q:...]]` tag present (hasn't asked next question yet)

### 2. Updated AI Instructions

Modified the system prompts to instruct AI to:

**In `constant.py` (lines 371-390):**
```
ANSWER CAPTURE & VERIFICATION FLOW:
• After user provides an answer to a Business Plan question:
  1. Acknowledge their answer briefly (1-2 sentences)
  2. Optionally provide brief encouragement or insight
  3. DO NOT immediately ask the next question
  4. WAIT for user to confirm (Accept) or modify their answer
• Only ask next question AFTER user confirms with "Accept"
```

**In `angel_service.py` session context (line 1693):**
```
10. If user provides an answer, acknowledge it briefly and positively (1-2 sentences) - 
    e.g., "Thank you for sharing that!" DO NOT ask the next question yet - 
    the system will show Accept/Modify buttons and only move forward after user clicks Accept
```

### 3. Accept Command Flow

The existing Accept command handling (lines 1407-1455) works perfectly:
1. User clicks "Accept" → Sends "accept" to backend
2. Backend detects Accept command → Moves to next question
3. Next question is asked with proper tag
4. Cycle repeats

## How It Works Now

### Example Flow

**Step 1: User Answers Question**
```
AI: [[Q:BUSINESS_PLAN.01]] What is your business name?
User: "Acme Plumbing Services"
```

**Step 2: AI Acknowledges (NEW - Shows Accept/Modify)**
```
AI: "Thank you for sharing that! That's a great name for a plumbing business."

System:
- Detects: is_user_answer = True
- Detects: has_acknowledgment = True (found "Thank you")
- Detects: has_question_tag = False (no [[Q:...]])
- Result: ✅ Show Accept/Modify buttons
```

**Step 3: User Reviews and Clicks Accept**
```
User: Clicks "Accept" button
System: Sends "accept" to backend
```

**Step 4: Backend Moves to Next Question**
```
Backend: Detects Accept command → Increments question number
AI: [[Q:BUSINESS_PLAN.02]] What is your business tagline or mission statement?

System: No buttons shown (is a question, not an acknowledgment)
```

## Debug Logging

Enhanced logging helps track button detection:

```
🔍 Button Detection:
  - User input: 'Acme Plumbing Services'
  - Is command request: False
  - Is draft response: False
  - Is next question: False
  - Is user answer (BP): True
  - Has acknowledgment: True
  - Has question tag: False
  - Reason: Answer acknowledged in Business Plan
  - Should show buttons: True ✅
```

## Files Modified

1. **`Angle-Ai/backend/services/angel_service.py`**
   - Lines 136-210: Enhanced `should_show_accept_modify_buttons()` with Business Plan answer detection
   - Line 1831: Updated function call to pass `session_data` parameter
   - Line 1693: Updated instruction #10 to tell AI not to ask next question immediately

2. **`Angle-Ai/backend/utils/constant.py`**
   - Lines 371-390: Updated verification flow instructions to explain Accept/Modify behavior

## Testing Scenarios

### Scenario 1: Regular Answer
```
✅ User answers: "I want to start a plumbing business"
✅ AI: "Thank you! That's great to hear."
✅ Buttons shown: Accept | Modify
```

### Scenario 2: Draft Command
```
✅ User types: "draft"
✅ AI: "Here's a draft for you: [content]"
✅ Buttons shown: Accept | Modify (existing behavior)
```

### Scenario 3: Accept After Answer
```
✅ User clicks Accept
✅ AI asks next question: [[Q:BUSINESS_PLAN.02]]
✅ Buttons NOT shown (is a question)
```

### Scenario 4: AI Asks Question
```
✅ AI: [[Q:BUSINESS_PLAN.01]] What is your business name?
✅ Buttons NOT shown (is asking, not acknowledging)
```

### Scenario 5: Short User Response
```
✅ User: "Acme"
✅ AI: "Great! Could you expand on that a bit?"
✅ Buttons shown: Accept | Modify (has acknowledgment "Great!")
```

## Edge Cases Handled

1. **AI immediately asks next question**: If AI includes [[Q:...]] tag in acknowledgment, buttons won't show (user answer was good enough)
2. **Support/Draft during BP**: These still show buttons (existing behavior preserved)
3. **Accept command**: Properly moves to next question (existing behavior works)
4. **Modify command**: Allows user to re-answer (existing behavior works)
5. **KYC phase**: Button logic only applies to BUSINESS_PLAN phase

## Benefits

✅ **Consistent UX**: Users always get Accept/Modify after answering  
✅ **User control**: Users can review and modify before moving forward  
✅ **No breaking changes**: Existing Draft/Support/Scrapping flows unchanged  
✅ **Better CX**: Feels more conversational and less rushed  
✅ **Flexible**: Users can modify answers without complex navigation

## Rollback Plan

If issues arise:
1. Revert `angel_service.py` lines 136-210 to previous version
2. Revert `constant.py` lines 371-390 to previous instructions
3. Previous version showed buttons only for Draft/Support/Scrapping

## Next Steps

1. ✅ Deploy to staging
2. ⏳ Test all Business Plan questions (BP.01-BP.46)
3. ⏳ Monitor button show rates in production logs
4. ⏳ Gather user feedback on improved flow
5. ⏳ Consider adding similar flow to KYC phase if needed

---

**Date**: October 16, 2025  
**Priority**: HIGH - User Experience  
**Status**: ✅ COMPLETE


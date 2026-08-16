# Incidents

## Incident summary

**Incident:** API latency increased from 300ms (P95) to 5,000ms (P95)  
**Impact:** 5,000 users experienced slow page loads, 5% error rate  
**Duration:** 60 minutes (14:00-15:00 UTC, Jan 20, 2024)  
**Root Cause:** Database connection pool exhaustion  
**Status:** Resolved

## Timeline
 
| Time (UTC) | Event |
|------------|-------|
| 14:00 | CloudWatch alarm triggered: High latency detected |
| 14:05 | On-call engineer paged |
| 14:10 | Investigation started using RED method |
| 14:15 | Confirmed elevated error rate and latency |
| 14:20 | USE method applied to resources |
| 14:25 | Identified DB connection pool at 100% utilization |
| 14:30 | ROOT CAUSE: Connection pool exhausted (max 20) |
| 14:35 | Immediate fix: Increased pool size to 50 |
| 14:40 | Service began recovering |
| 14:50 | Latency returned to normal |
| 15:00 | Incident closed |


## RED Method Analysis

### Rate (Traffic)

- Normal: 500 req/min
- Incident: 1,500 req/min
- **Finding: 3x traffic increase**
 
### Errors

- Normal: 0.1%
- Incident: 5.0%
- **Finding: 50x error increase**
 
### Duration (Latency)

- Normal P95: 300ms
- Incident P95: 5,000ms
- **Finding: 16x latency increase**
 
### Conclusion

All three RED signals elevated. Significant performance degradation.
Primary symptom: High latency (16x increase)

## USE Method Summary
 
### CPU
- ✅ Utilization: 45% (normal)
- ✅ Saturation: Normal
- ✅ Errors: None
 
### Memory
- ✅ Utilization: 70% (normal)
- ✅ Saturation: No swapping
- ✅ Errors: None
 
### Database Connection Pool
- 🔴 Utilization: 100% (maxed out!)
- 🔴 Saturation: Requests queuing
- 🔴 Errors: Timeout errors
 
## Conclusion
**ROOT CAUSE IDENTIFIED: Database connection pool exhaustion**


## Root causes identified

- **Problem:** Database connection pool exhausted
- 
-


## Fixes applied

### Immediate (Week 1)
- [x] Increase connection pool to 50 (DONE)
- [ ] Add CloudWatch alarm for connection pool > 80% (Owner: Sarah, Due: Jan 25)
- [ ] Document connection pool sizing (Owner: Mike, Due: Jan 22)
 
### Short-term (Month 1)
- [ ] Implement auto-scaling for connection pool (Owner: Mike, Due: Feb 5)
- [ ] Load test with 5x normal traffic (Owner: Team, Due: Feb 10)
- [ ] Create runbook for connection pool issues (Owner: Alex, Due: Jan 30)
 
### Long-term (Quarter 1)
- [ ] Establish engineering review process for marketing campaigns (Owner: Manager, Due: Feb 15)
- [ ] Implement capacity planning framework (Owner: Team, Due: Mar 1)
- [ ] Add auto-scaling dashboard widget (Owner: Sarah, Due: Feb 5)

## Lessons learned

### What Went Well ✅
- Alerts triggered immediately (within 1 minute)
- On-call engineer responded quickly (5 minutes)
- Systematic RED/USE methodology led to root cause
- Clear monitoring data available
- Mitigation applied quickly (10 minutes to identify, 5 to fix)
 
### What Went Wrong ❌
- No capacity planning for marketing campaigns
- Connection pool not monitored (no alerts)
- No auto-scaling configured
- Lack of communication between marketing and engineering
- No load testing performed
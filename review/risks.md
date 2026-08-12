# Risks

## Shared room risks

- 공유 방 코드는 전달될 수 있으므로 위치 식별자로만 취급하고, 목록 수정과 방장 추첨에는 별도의 추측 불가능한 참가자 토큰을 요구한다.
- 닉네임은 검증된 신원이 아니다. 길이와 문자를 제한하고 방 안에서 대소문자를 무시해 중복을 막으며 클라이언트에서 이스케이프한다.
- 서버리스 인스턴스의 메모리는 참가자 상태를 신뢰성 있게 유지할 수 없다. 방 상태를 PostgreSQL에 저장하고 제한된 폴링을 사용한다.
- 입장, 목록 저장과 추첨이 동시에 일어날 수 있다. 변경 작업은 트랜잭션과 행 잠금을 사용하고 완료 상태와 득표를 그 안에서 다시 계산한다.
- 중복 메뉴가 하나도 없는 방은 그럴듯한 당첨을 만들면 안 된다. 레버를 잠그고 API도 명시적인 `no_overlap` 충돌을 반환한다.
- 방치된 방과 폴링은 저장량·조회량을 키울 수 있다. 방은 24시간 뒤 만료하며 오래된 행 자동 정리는 운영 후속 작업으로 남긴다.

## Product and data

- A reroll can mean dislike, unavailability, cost, distance, or mood. It therefore has only a weak negative weight.
- Seed-food attributes and rice/bread/noodle memberships are editorial estimates, not nutritional or restaurant-availability facts.
- Anonymous local identity does not synchronize; signed-in history does.
- Initial production data is too sparse for qualified collaborative edges, so `rules-v4` remains content-led until five authenticated accounts overlap on a food pair; no claim of measured lift is made yet.
- A five-account threshold limits noise and disclosure but does not eliminate coordinated account manipulation; cosine correction and confidence shrinkage reduce its impact.

## Engineering

- SQLite and the live Neon PostgreSQL runtime are verified; the optional Docker Desktop PostgreSQL development path is not.
- Automated browser E2E coverage is not configured yet.
- The browser token is stored in local storage and is exposed if an XSS flaw is introduced.
- Throttling uses Django's default per-instance cache and is only a basic abuse barrier on serverless instances.
- The 365-day authenticated event scan is cached for five minutes; it should move to a precomputed affinity table only after measured latency or event volume justifies it.
- Node emits a non-failing upstream deprecation warning during the Nuxt build.

## Mitigations

- Preserve exact exposure and policy data for later evaluation.
- Keep policy changes versioned and reasons tied to real score factors.
- Measure content-only versus collaborative-qualified acceptance and reroll rates before changing the 15% collaborative weight.
- Treat dietary restrictions as future hard filters, never as soft preferences.
- Complete email verification, reset/deletion flows, privacy/operator details, and secure-cookie hardening before inviting real users.

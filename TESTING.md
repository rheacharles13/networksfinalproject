# TESTING.md for Final Project

# Benjamin Vazzana (bav2113), Rhea Charles (rtc2133), Shinjini Mukherjee (sm5160), Shreeya Patel (sjp2236)

# Testing Blockchain Meal Swipe Exchange Application

This document outlines test cases for testing the blockchain system with a focus on meal swipe exchanges. The system allows members to donate up to 150 meal swipes. Additionally, the test cases include scenarios for adding new members to the network.

## Test Cases

### 1. **Test Member Registration and Addition**

**Objective**: Ensure that new members can be added to the blockchain system successfully.

#### Steps:
1. Start the tracker and all peers.
2. Add a new member to the blockchain system (e.g., Member1).
3. Verify that the new member is correctly registered in the system.
4. Check the member's balance to ensure it's initialized correctly (e.g., 150 meal swipes).

#### Expected Result:
- The new member should be added to the system and appear in the list of registered members.
- The member should have a starting balance of 150 meal swipes.

#### Attempted Input:
#### Actual Result:

---

### 2. **Test Meal Swipe Donation (Within Limit)**

**Objective**: Verify that a member can donate meal swipes within the limit of 150.

#### Steps:
1. Start the tracker and peers.
2. Member1 donates 50 meal swipes to another member (e.g., Member2).
3. Verify that Member1's balance is updated to 100 swipes (150 - 50).
4. Verify that Member2's balance is increased by 50 swipes.

#### Expected Result:
- Member1 should have a new balance of 100 meal swipes after the donation.
- Member2 should have received 50 meal swipes, increasing their balance appropriately.

#### Attempted Input:
#### Actual Result:
---

### 3. **Test Meal Swipe Donation (Exceeds Limit)**

**Objective**: Ensure that a member cannot donate more meal swipes than their balance (150 limit).

#### Steps:
1. Start the tracker and peers.
2. Member1 attempts to donate 200 meal swipes to Member2.
3. The system should reject the donation due to insufficient swipes.
4. Verify that Member1's balance remains unchanged.

#### Expected Result:
- The system should prevent Member1 from donating more than their available meal swipes.
- Member1's balance should remain at 150, and no transfer should take place.

#### Attempted Input:
#### Actual Result:
---

### 4. **Test Meal Swipe Donation Between Multiple Members**

**Objective**: Test the ability of multiple members to donate meal swipes to each other, ensuring proper balance updates.

#### Steps:
1. Start the tracker and peers.
2. Member1 donates 30 meal swipes to Member2.
3. Member2 donates 20 meal swipes to Member3.
4. Verify the balances after the transactions:
   - Member1: 120 swipes
   - Member2: 100 swipes (after receiving 30 from Member1 and donating 20 to Member3)
   - Member3: 20 swipes (after receiving 20 from Member2)

#### Expected Result:
- The balances of each member should be updated correctly after the transactions:
  - Member1: 120 swipes
  - Member2: 100 swipes
  - Member3: 20 swipes

#### Attempted Input:
#### Actual Result:

### 5. **Test Forking Scenario - Simultaneous Transactions**

**Objective**: Simulate a forking situation where two users enact a transaction at the same time, and only one of them is confirmed and accepted into the blockchain, demonstrating the handling of conflicting transactions.

#### Steps:
1. Start the tracker and peers.
2. Member1 and Member2 each attempt to donate 50 meal swipes to Member3 at the same time.
   - Member1 sends a transaction donating 50 swipes to Member3.
   - Member2 sends a transaction donating 50 swipes to Member3.
3. Both transactions are broadcasted to the network at almost the same time, creating a fork in the blockchain.
4. The system should choose only one of the transactions (based on longest chain rule), and the other transaction should be rejected.
5. Verify that only one transaction is confirmed, and Member3’s balance is increased by 50 swipes.
6. Verify that Member1 and Member2’s balances reflect the correct deductions (either one donor's balance decreased by 50 swipes or both balances unchanged if one transaction was rejected).

#### Expected Result:
- One of the transactions should be successfully added to the blockchain and confirmed.
- The other transaction should be rejected (indicating a fork resolution).
- Member3’s balance should increase by only 50 meal swipes, reflecting one successful donation.
- Only one of the donors (either Member1 or Member2) should have their balance decreased by 50 meal swipes.
- The blockchain should resolve the fork by selecting the valid transaction (using the consensus protocol like the longest chain rule or another mechanism).

#### Attempted Input:
#### Actual Result:

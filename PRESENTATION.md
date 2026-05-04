# Prediction Markets Research Assistant - Live Demonstration

## 1. Introduction (1 min)
* **Hook:** "Welcome to our Prediction Markets Research Assistant. Information is moving faster than ever, and prediction markets like Kalshi and Polymarket are at the forefront of this speed. But the challenge is: How do you identify real opportunities when there are hundreds of markets updating by the second?"
* **Value Proposition:** "We built a multi-agent AI pipeline that automatically parses live markets from Kalshi and Polymarket, categorizes them, compares cross-platform spreads, and grounds its strategy in academic research (Wolfers & Zitzewitz, 2006)."
* **Stakeholder Value:** "This gives quantitative researchers and retail traders an instant, data-backed assessment of where the highest probability, fee-exploitable trades are right now."

## 2. App Walkthrough & Clarity (2 mins)
* **Action:** Click "Run Full Analysis" to initiate the pipeline.
* **Explanation:** 
    * "Notice the real-time feedback at the bottom. Our pipeline runs 3 AI Agents sequentially: Collector (fetching markets), Classifier (categorizing), and Strategist (analyzing)."
    * "The design is meant to be streamlined—there are no confusing settings. Just a single button to run the analysis, and immediate visual categorization of sectors like Politics, Sports, and Finance."
* **Efficiency:** "The entire analysis takes only a few seconds, preventing analysis paralysis."

## 3. Deep Dive (1 min)
* **Action:** Select a sector (e.g., 'sports' or 'politics') and click "Analyze [Sector] Trades".
* **Explanation:** "Here, Agent 3b takes over. It performs a deep dive, checking for cross-platform matches and comparing the 'mid-price' spread. The AI tells us exactly what to do—for instance, 'BUY YES on Kalshi' and 'SHORT YES on Polymarket'—while warning us of risks and whether the spread actually clears the platform fees."

## 4. Quality Control & Validation (1 min)
* **Action:** Scroll down to the "AI Quality Control & Validation" panel.
* **Explanation:** 
    * "We didn't just build an AI tool; we built a *reliable* AI tool."
    * "As you can see in our QC Panel, we track the latency and the schema success rate for every single agent run."
    * "If an LLM hallucinates or returns malformed JSON, our system catches the parse error and reports it immediately. We enforce strict schema validation to ensure the data presented to the user is 100% formatted correctly."
    * "This guarantees our app doesn't break silently—providing evidence that our prompting strategy works effectively."

## 5. Conclusion
* **Summary:** "To summarize, our app takes the chaos of live prediction markets and turns it into structured, academically-grounded trading signals with built-in quality control."
* **Q&A:** "Thank you. We'd be happy to take any questions."

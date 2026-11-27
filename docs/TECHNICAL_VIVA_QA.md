# CodeAssessment Technical Viva & Review Defense Guide

**Prepared by:** Kantam Pavan Sai Reddy (DevOps & Infrastructure Lead)  
**Target Review:** Capstone & Research Presentation Review  

---

### Q1: Why did you decouple the LLM from the grading authority?
**Answer:**  
In computing education literature (Prather et al. 2023, Becker et al. 2023), pure LLM graders exhibit significant non-deterministic score drift ($\sigma^2 = 14.8$) and are susceptible to prompt injection via student comments. In CodeAssessment, we established a **Mixed-Evidence Model**: correctness and complexity scores are computed deterministically by containerized test verdicts and Tree-sitter AST analysis ($\sigma^2 = 0.0$). Generative LLMs are strictly confined to non-grading roles: explaining compiler errors, suggesting hints, and recommending roadmap topics.

---

### Q2: Why can't we just measure wall-clock execution time to find Big-O?
**Answer:**  
Wall-clock execution time and peak memory are non-deterministic: they are corrupted by OS CPU scheduling jitter, Python/JVM warm-up time, container virtualization overhead, and garbage collection pauses. A single slow run on an autograder cannot prove asymptotic complexity. Instead, we use a **hybrid tri-tier approach**: our static Tree-sitter analyzer examines the syntax tree for loop nesting depth, divide-and-conquer logarithmic steps, recursion trees, and allocation calls, comparing them against an audited 10-level asymptotic ladder ($O(1)$ to $O(n!)$).

---

### Q3: What is the 79.0% Correctness Gating Cap and why is it needed?
**Answer:**  
In a multi-dimensional rubric (Correctness, Time, Space, Style), a student could write code that is syntactically elegant and theoretically optimal but fails fundamental functional test cases. Without a cap, that incorrect code could score 85% or 90% purely on style and complexity marks. Our policy enforces:
$$S_{\text{final}} = \begin{cases} S_{\text{raw}}, & \text{if } C = 100.0 \\ \min(S_{\text{raw}}, \; 79.0), & \text{if } C < 100.0 \end{cases}$$
This mathematically guarantees that no non-working code can achieve a first-class or distinction grade.

---

### Q4: How is Docker sandboxing configured to prevent security breaches?
**Answer:**  
We execute student code inside ephemeral Docker containers (`python`, `c`, `cpp`, `java`). Each container is hardened with:
1. Non-root user privileges (`user: runner`).
2. Disabled networking (`--net=none`) to prevent socket binding, port scanning, or external data exfiltration.
3. Read-only root filesystems, writing only to a temporary in-memory tmpfs mount.
4. Resource caps: 1.0 vCPU core, 256MB RAM, and a hard 5.0-second CPU execution timeout.

---

### Q5: What happens if Groq API goes down or hits a rate limit?
**Answer:**  
The pipeline has zero downtime. Our `explainability_node` detects provider exceptions and automatically triggers `build_evidence_feedback()`. This deterministic fallback parses the compiler error messages, failing test assertions, and AST loop structures directly into structured markdown advice in under 450 milliseconds without requiring any third-party network call.

---

### Q6: What is the difference between a Verified and a Hypothetical Score Projection?
**Answer:**  
A hypothetical projection calculates what the student's score *would* be if they fixed correctness to 100% under their existing complexity and style. A verified projection, however, occurs when the backend privately compiles and executes the refactored code against the official judge suite, confirming that every test case passes before displaying a verified score gain.

---

### Q7: Why did you colocate your PostgreSQL database in Mumbai (ap-south-1)?
**Answer:**  
In our initial prototype, our database was hosted in US-East (`us-east-1`), resulting in a single-query round-trip latency of 553.9 ms and test suite execution time of 28.5 seconds. By migrating the database to Supabase Mumbai (`ap-south-1`), TLS handshakes dropped by 89.1%, single query latency fell by 92.2% down to 43.18 ms, and our automated test suite execution speeded up by 83.5% (4.7 seconds).

# Defects in the staged textbook pages

The staged pages are Tan, Steinbach and Kumar, *Introduction to Data Mining*, 1st edition (2006). Students do not use the book, and the notes are written in our own words. Where the pages have a defect, the notes use the correct form, and the source check will report a DIFFERS. Keep the notes' form and list it in the report.

## Margin notes in the PDFs

The staged PDFs carry handwritten notes by the author, for example "More expnsive than taking large sample right away", "Meaningless", "Sum over j, not i". They are not book text. Tell the source-check agent so.

## Chapter 2

| Place | The staged page | The notes use |
|---|---|---|
| 2.3.6, binarization | n = log₂(m) binary digits | n = ⌈log₂ m⌉ (5 values need 3 digits) |
| 2.3.6, entropy | the sum over i = 1..k, and no minus sign in the extracted text | eᵢ = −Σⱼ pᵢⱼ log₂ pᵢⱼ, with 0 log₂ 0 = 0 |
| 2.3.6, interval notation | "x₀ and xₙ may be +∞ or −∞, respectively" (puts +∞ first) | x₀ = −∞ and xₙ = +∞ |
| 2.3.6, Example 2.12 | K-means best, then equal frequency, then equal width, on one dataset | the same ranking, stated as one comparison, not a general rule |
| 2.3.7, absolute standard deviation | σA = Σ \|xᵢ − μ\| (no 1/m) | σA = (1/m) Σ \|xᵢ − μ\|, so it does not grow with m |
| 2.4.1, d/(1 + d) | 10 → 0.90 (cut off) | 0.909 (rounded) |
| 2.4.5, Example 2.18 | ‖y‖ = 2.24 | √6 = 2.45; the cosine 0.31 is right |
| 2.4.6, Eq. 2.16, weighted similarity | Σ wₖδₖsₖ / Σ δₖ with Σ wₖ = 1, which gives 1/n instead of 1 when every sₖ = 1 | Σ wₖδₖsₖ / Σ wₖδₖ, which gives 1 and reduces to Eq. 2.15 with equal weights |

## Chapter 3 (staged pages are the 2nd edition)

The Module 3 textbook PDFs (`m03_ch03-*`) are the 2nd edition (2019), not the 1st: section 3.3 is "Decision Tree Classifier".

| Place | The staged page or deck | The notes use |
|---|---|---|
| Deck slide 45, entropy of (1, 5) | `– (1/6) log2 (1/6) – (5/6) log2 (1/6) = 0.65` | −(1/6) log₂(1/6) − (5/6) log₂(5/6) = 0.650 |
| Deck slide 37/49, {Sports, Luxury} vs {Family} | Gini 0.468 | 0.469 (0.46875); the author's margin note has 0.469 |
| Deck slides 49–50 | margin notes "Gain Ratio = 0.163/1.522" | not book text: the gain ratio divides the gain, not the weighted Gini |
| 3.3.2, continuous test | written `A < v` (and `Annual Income ≤ τ` later) | `A ≤ v`, and the notes say both forms are in use |
| 3.3.6, parity | "a full decision tree with 2^d nodes" | 2^d leaves (a full tree has 2^(d+1) − 1 nodes) |
| Example 3.4, gain ratio of Car Type | 0.620 / 1.52 = 0.41 | not used; the notes use the grocery data |
| 3.6.2, leave-one-out | "every run uses exactly one data instance for testing and the remainder of the data for testing" (the second "testing" should be "training") | the rest of the data for training |
| 3.5.3, Eq. 3.13 | "α is the confidence level" | α sets the confidence level of the bound; with α = 0.25, z = 1.150 |

## Chapter 5 (cluster analysis)

| Place | The staged page | The notes use |
|---|---|---|
| 5.4.1, "Core points", on Figure 5.21 | point A, with 7 points within Eps, "is a core point for the radius (Eps) if MinPts ≥ 7" (it should be MinPts ≤ 7; the definition just before it is right) | a core point has at least MinPts objects within Eps, itself included |
| 5.4.2, "Clusters of Varying Density" | a stray word "true" in the extracted text of the paragraph on Figure 5.24 (an artifact of the figure) | not used |
| 5.5.6, Hopkins statistic, Eq. 5.17 | H = Σw / (Σu + Σw), and the sentence "values near 0 and 1 indicate highly clustered and regularly distributed data" matches that form; but the example values (0.56 for random data, 0.95 for well-separated clusters) need Σu on top | H = Σu / (Σu + Σw): clustered data near 1, random near 0.5, evenly spread near 0; the notes say that some texts use the other form |
| 5.5.3, "General Comments", silhouette against K | measures that combine cohesion and separation "will tend to decrease until the natural set of clusters is found and start increasing once clusters are being split too finely" | a measure for which higher is better (the silhouette) tends to peak at the natural K; one for which lower is better (the SSE) falls fast until then and slowly after |
| 5.5.3 and 5.5.6 | the author's margin notes and web addresses (for example "If each point is a cluster, silhouette coefficient is 1", "Create an exercise to demonstrate this") | not book text |

## Chapter 6 (classification: alternative techniques), and the Module 5 decks

Confirmed by the Module 5 source checks (2026-11-14). The staged Chapter 6 pages are the 2nd edition.

| Place | The staged page | The notes use |
|---|---|---|
| 6.4.2, naive Bayes | "reduced from dk to dk" (a lost superscript: k^d to dk; the same quantity prints as k^d earlier) | d × k instead of k^d |
| Naive Bayes deck, slide 16 (Tid 7 deleted) | "If class = No" printed twice; the second (mean 90, variance 25) is class Yes | class Yes: mean 90, variance 25 |
| Bayesian-network inference deck | P(HD=No \| E=No, D=Yes) printed as 0.45; the computation uses 0.55 | 0.55 |
| Heart-disease network: textbook Figure 6.13 against the naive Bayes deck | the textbook's table has 0.55 at (E=No, D=Healthy) and 0.45 at (E=Yes, D=Unhealthy); the deck's table swaps them, and its inference uses the deck's values | an invented store network (neither table) |
| Nearest-neighbor and naive Bayes decks | title "Chapter 4"; the staged chapter is 6 (printings differ) | no chapter numbers |
| 6.4.2, Gaussian class-conditional | the Gaussian value is called a probability, P(Xi = xi \| Y) = … | a density; the notes say some texts call it a probability, and that only the comparison between classes matters |
| 6.7.1, perceptron rule (page 454) | "If ŷ = 0 and y = 1 … if ŷ = 1 and y = 0", although Eq. 6.48 and the sign function use −1 and +1; and "the weight … associated with the i-th input link", although the index is j | ±1 labels, so the error e = y − ŷ is ±2; the index j |
| 6.8.3, dropout | the scaled model (w*, b*) = (1 − γ)(w, b) scales every weight and the bias terms | the notes' networks scale only the weights leaving droppable nodes, and say how the book's form differs |
| 6.9.2, margin | "if k+ = k− = M, then margin = k+ − k− = 2M" (k− > 0) | k+ + k− |
| Figure 6.35 | B1's second margin hyperplane labelled "b21" | b12 |
| 6.9.3, soft margin | every object with ξ > 0 is called misclassified | 0 < ξ ≤ 1: inside the margin, still correct; ξ > 1: a training error; the notes say some texts call every ξ > 0 misclassified |
| 6.9.5, item 3 | the RBF SVM's test error "gradually declines and eventually reaches close to 0.5" with 125 irrelevant attributes | it rises toward 0.5 |
| 6.10.6, out-of-bag | "the remaining 27% of base classifiers" (three times; 100 − 63 = 37) | about 37 % |
| Eq. 6.102 and Algorithm 6.6, AdaBoost error | a 1/N factor in front of Σ w δ, although the weights sum to 1 (Figure 6.50's α = 1.738 uses it) | ε = Σ w δ, with the weights summing to 1 |
| Eq. 6.106 and the weighted-accuracy table | Fβ denominator (β²+1)TP + β²FP + FN, and the Fβ row's FP and FN weights, swapped; the recall and precision rows of the table swapped | (β²+1)TP + β²FN + FP; recall weights FN, precision weights FP |
| 6.11.4, p. 528 (printed so) | a random classifier's FPR "(pn−)/p = p" | (p n−)/n− = p |
| Figure 6.45 | caption about L2 and L1 norms; the text uses the figure for overfitting and underfitting | not cited |
| 6.12, ECOC | "any (d − 1)/2) errors" (no floor, stray parenthesis); "the 1-r approach given in Example 6.12" (it is 6.11) | ⌊(d − 1)/2⌋ |
| Chapter 6 introduction | promises cost-sensitive classification in 6.11.2, which has none | the cost section is the course's own (not in the staged pages) |
| 6.9.3 and Eq. 6.91 (extraction only) | the extracted text shows "ξ/w" and drops a square root; the printed page has ξ/‖w‖ and the root | not defects: look at the PDF page before you report one |

## Chapter 8, unit 1 (soft and probabilistic clustering), and its deck

The staged Chapter 8 pages are the 2nd edition (spectral clustering is 8.4.5).

| Place | The staged page or deck | The notes use |
|---|---|---|
| Soft-clustering deck, slide 6 (checked on the PDF page) | "SSE(x) has a minimum value of 1.654 when wx1 = 0.74, wx2 = 0.36" (the weights add up to 1.10) | \( w_1 = 6.25/8.5 = 0.735 \), \( w_2 = 0.265 \), SSE 1.654 |
| 8.2.2, Example 8.4 | prob(distribution 1 \| 0) = 0.12/(0.12 + 0.06) = 0.66 (it is 0.667) | not used; the notes use the store's baskets |
| 8.2.1, the fuzzifier | "as p gets larger, all the cluster centroids approach the global centroid" | true in the limit; on the store the centroids stay in the three groups up to \( p = 25 \) while the weights approach \( 1/K \); the notes say both |
| 8.2.2, mixture weight | written \( w_j \), the letter of the fuzzy weight \( w_{ij} \) | \( P(C_j) \), as the deck writes it; the notes say that some texts write \( w_j \) |

## Not staged

- Appendix B (PCA and SVD in detail). The PCA worked example in unit 2 is from own knowledge, approved by the author, and listed as such.

## Chapter 8 (cluster analysis: additional issues), and the Module 6 decks

Found while writing Module 6 unit 2 (2026-11-14). The staged Chapter 8 pages are the 2nd edition (spectral clustering is Section 8.4.5). They carry many margin notes by the author (for example "Wouldn't it work without spectral clustering? It seems that the graph has two connected subgraphs.", "Why not choose MIN_SIZE=1?", "Does this reqyure sparsification of the original proximity matrix?"); the notes answer several of them in "Questions people ask".

| Place | The staged page or deck | The notes use |
|---|---|---|
| Graph-based deck, slide 57 (Laplacian) | "all eigenvalues are positive" and "Last eigenvalue is 0" | eigenvalues are 0 or more (the textbook's "non-negative"); the smallest is 0 (eigenvalues sorted smallest first) |
| 8.4.9 and the deck, SNN core point | "exceeds a certain threshold MinPts" (textbook), "SNN density greater than MinPts" (deck) | at least MinPts, as for DBSCAN in Module 4; the SNN density does not count the object itself |
| 8.4.7 and the deck, Jarvis-Patrick | "share more than T neighbors" (deck); "shared at least 10 points" (textbook example) | at least T; the notes say that "more than T" is the same rule with T one smaller |
| 8.3.3, DENCLUE step 6 | "connected by a path of points" with density ≥ ξ, path not defined | the notes check the straight line between two attractors, and say so |
| 8.4.4, EC(Ci) | the minimum-cut bisection (METIS) | balanced bisection by the second Laplacian eigenvector, stated as a stand-in |
| 8.3.2, CLIQUE monotonicity | stated forward (a cluster in k dimensions is a cluster in every subset); the deck states the contrapositive | both forms |

## Chapter 10 (avoiding false discoveries), and the Module 7 deck

Found while writing Module 7 (2026-11-16). The staged chapter is the 2nd edition. It carries the author's margin notes ("Skip" at 10.4, "Teach in class" at 10.5, and questions such as "Why not decrease p as the dataset becomes larger?", "Where does 45 come from?", "The test set does not change?"); the notes answer them in "Questions people ask".

| Place | The staged page or deck | The notes use |
|---|---|---|
| Deck, slide 27 (FWER) | "If m = 10, FWER = 0.60" | \( 1 - 0.95^{10} = 0.401 \) |
| Deck, slide 15 (coin) | "for R >= 8, p = .044 + .01 + .001 = .055"; "for R >= 9, p = 0.01 + 0.01 = 0.011" | exact values \( P(R \ge 8) = 0.0547 \), \( P(R \ge 9) = 0.0107 \) (a Questions entry) |
| 10.1.2, Definition 10.5 (extracted text) | "β = P(R ∈ Critical Region \| H1)" | \( \beta = P(R \notin \text{critical region} \mid H_1) \); the ∉ may be lost in extraction |
| 10.5.3, Table 10.5 | title "Beverage preferences among a group of 1000 people"; row and column labels do not match the neighborhood example | not used; enrichment is in "Take it further" |
| 10.1.3, after Eq. 10.2 | "the number of actual positives … m0, is very small compared to the number of actual negatives, m1" (m0 and m1 swapped; Table 10.1 has m0 for H0) | \( m_0 \) = results with \( H_0 \) true, as in Table 10.1 |
| 10.3.2 | "labeled as positive … in order to maximize the FDR" (should be control or minimize) | not used |

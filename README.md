# Sabermetrics-Terminal-Pitch-Count

We imagine a scenario where a MLB team manager or hitting coach ask what adjustments can be made to their team's hitting strategy to help improve their chance to win.  Without changing the roster, the strategy cannot easily change by converting some singles into doubles, or doubles into home runs.  Instead, they can only change how aggressive or patient the team is at different pitch counts.  Adjusting these tendencies would manifest in the terminal pitch counts (pitch count when an at-bat ends) of the team over the course of a season.


## Background Information

Throughout this project, we will be referring to various pitch counts throughout an at-bat.  A batter's count is the number of balls and strikes the batter has seen in a particular at-bat, written in the form balls-strikes.  Starting at 0-0, the pitch count will change over the course of an at-bat as more pitches are thrown to the batter.  When considering the terminal (pitch) count, we are only considering the final pitch count for that particular batter before the end of an at-bat; The pitch count before the final pitch was thrown in an at-bat.  An important consequence of this is on strikeouts and walks.  If the batter reaches three strikes, resulting in a strikeout, the terminal pitch count would be recorded as having 2 strikes.  Similarly a fourth ball, resulting in a base-on-balls (walk), would be recorded as having a terminal pitch count with 3 balls.  Consequently, the "largest" count that can be reached during an at-bat is 3-2, at which point the terminal pitch count for that at-bat must be 3-2.

Once a particular count is reached, the only counts that can be reached later in that particular at-bat have at least as many balls and strikes.  As an example, consider the possible pitch counts that are achievable after a 2-1 count: 3-1, 2-2, 3-2.  Within the context of the problem at hand, consider the effect of being more aggressive and swinging at 2-1 pitches more often.  Acquiring this more aggressive strategy would increase the number of balls-in-play at the 2-1 count at the cost of decreasing the number of at-bats reaching 3-1, 2-2, and 3-2 pitch counts.  Conversely, being more patient on 2-1 counts will mean a decrease in the amount of balls-in-play on 2-1 pitches, increasing the number of at-bats reaching counts of 2-2, 3-1, and 3-2.


### Why should terminal pitch count play a role in a team's success?

At surface level, the more pitches the average batter sees in an at-bat, the more pitches the opposing pitcher needs to throw.  Fatigue across the opposing team's entire pitching staff will generally produce more mistakes for the batters to exploit.  On the flip side, an aggressive team, that is always looking to swing, will take advantage of the opposing team's mistakes rather than trying to force more.  The question then becomes whether there is a clear trend in aggressive vs passive batting behavior, or if there are multiple strategies for teams to succeed with.

Furthermore, a batter will perform differently in different pitch counts.  When down in the count (more strikes than balls), the opposing pitcher has little incentive to throw a good, hitable pitch, but the batter is worried about striking out and will frequently swing at these poor pitches.  Conversely, when ahead in the count (more balls than strikes), a batter can wait for a good pitch to hit.  Therefore, the terminal pitch counts of teams could indicate whether a team is falling behind or staying ahead during an at-bat.


### Should Home and Away games be separated?

This question is briefly considered during the data exploration portion of the project.  Beyond the work done here, the effects of home-field advantage have been [considered in detail](https://sabr.org/journal/article/home-field-advantage/), and the home team wins roughly 54% of the time over 100 years of baseball.  In general, teams perform differently during home and away games, and different strategies may be imposed for these two classifications of games.


## General Methodology

### Direct application of terminal pitch counts

Starting with all play-by-play data files from the 2000 to 2009 MLB seasons, we extract the terminal pitch counts for each team's home and away games.  We then check for clusters of different strategies so that separate analysis can be done for each cluster, although only one cluster was found for each of the home and away data.  Finally, we use a Pythagorean Expectation model of the teams' win percentages.

With the model in hand, we can look at any specific team's terminal pitch count data, which describes the team's overall hitting strategy.  As an example, we will look at the 2007 Boston Red Sox, whose home and away terminal pitch count fractions are given by:

<p align="center">
 <img src="https://i.imgur.com/rjQ9wRj.png" width="504" height="288">
</p>

In this context, adjusting a team's hitting strategy means targetting a specific pitch count and trying to increase or decrease the number of times at-bats end at this count.  As mentioned in the Background Section, directly changing at the number of at-bats ending at a particular count will affect how often future counts (counts with more balls and strikes) are reached.  This interaction between pitch counts can be quantified using matrix transformations.  We are then able to simulateously check all single pitch count modified strategies (accounting for the inter-pitch count effects previously mentioned) we can then find which strategy results in the largest improvement of a team.

<p align="center">
 <img src="https://i.imgur.com/dnEahkt.png" width="504" height="288">
</p>

Here, we are able to show all single pitch count modifications for home and away data, and the net increase of wins.  Red squares indicate an aggressive modification will produce more wins, while a blue square indicates a patient modification.  By default, we modify the particular count by 1% of its original value, but the effects can be linearly scaled.  The optimal single-count adjustment can be summarized as:

<p align="center">
 <img src="https://i.imgur.com/bvF1GXO.png" width="622" height="136">
</p>

In this output, an aggressive change looks to increase the fraction of at-bats ending on a particular pitch count, while a patient change decreases the fraction. By default we look at a 1% change in a team's strategy, but since the models are linear in each of the pitch counts, one can scale the improvement for a large modification of the strategy.  However, the linear assumptions will eventually break down with large changes, and more accurate models would need to be implemented.


### Outcomes of individual at-bats

Directly modelling win percentage from terminal pitch count heavily relies on league averages to approximate the number of runs a team scores.  Doing this removes some of the nuance of hitting, or being a good hitter, and thus does a poor job of capturing a lot of the variation in the data.  As a result, we also look at how each terminal pitch count results in different outcomes, i.e. Strikeouts, Outs, Walks, Singles, Doubles, Triples, and Home Runs.  When modelling win percentage, we reduce the number of independent variables by only looking at the outcome of the at-bat, not which terminal count that outcome came from.

Similar to directly relating terminal pitch count to win percentage, this method effectively assigns a value to each terminal pitch count.  However, by specifically considering the (negative) value of a strikeout, the value of counts with 2 strikes is heavily penalized relative to every other count.

<p align="center">
 <img src="https://i.imgur.com/IxWGFKA.png" width="504" height="288">
</p>

As a result, nearly every team has the outcome that they should be patient on 2-2 pitch counts, since they stand to gain the most from that at-bat.  This speaks to the naive approach, where a batter is in complete control over whether they end an at-bat at a given pitch count.

Instead, we consider an aggressive strategy one where the batter is more likely to swing at pitches while a patient strategy is less likely to swing.  While these new definitions will have the same general trend of increasing or decreasing the number of at-bats ending in some pitch count, it more accurately assesses how much a hitter will need to adjust to get the desired outcome.

This new method of strategy adjustment is done by constructing a stochastic matrix and finding steady state solutions to the resulting Markov Chain given that each at-bat starts in a 0-0 count.  In addition to the computation cost of this new method, it also removes some of the linear properties of the strategy adjustment.  Thus, both aggressive and patient modifications must be considered separately for both home and away games. For both home and away, we find the following increase in win total when the team swings at 1% more (aggressive) or less (patient) of the pitches seen at that pitch count.

<p align="center">
 <img src="https://i.imgur.com/SkPl8DD.png" width="480" />
 <img src="https://i.imgur.com/JN1uk1P.png" width="480" />
</p>

The partial loss of linearity in this model makes it significantly more difficult to estimate large changes in strategy.  Instead, explicit calculation must be done for each proposed percentage change to a count.

<p align="center">
 <img src="https://i.imgur.com/7tj0M82.png" />
 <img src="https://i.imgur.com/cFXDz3x.png" />
</p>

As a result, it is often difficult to search the space for the maxmima in total wins and to find an efficient set of modifications to reach this maxima.


## Future Work

In every application of a strategy modification, we have ignored how these modifications will affect how other teams adjust their pitching strategy to counteract the change in hitting strategy.  For instance, if a team never swings at 3-0 pitch, other teams will naturally adjust and throw more strikes.  Incorporating this backreaction will introduce further non-linearities to the problem, and will likely establish non-extremal optimal strategies for different teams.

A similar analysis can be done to evaluate the pitching on a team.  This type of analysis would likely be needed in order to fully incorporate the backreaction effects.  However, incorporating a pitch analysis would allow us to remove the Runs Against statistic from the current analysis and potentially allow us to avoid some of the issue with using Pythagorean Wins in this model.

Finally, applying this analysis to more recent teams would give us access to pitch location data for a team.  Since this information is crucial for determining how swinging or not swinging impacts a team's performance, the approximations needed in this analysis could be significantly relaxed and a more accurate outcome would be possible.


## Files Included
#### Brief explanation

* DataExploration_ModelBuilding.ipynb: Jupyter Notebook containing start-to-end explanation of the data exploration and modeling process used in this problem.  Includes principal component analysis, clustering methods, and model building.

* StrategyAdjustment.ipynb: Notebook that finds the optimal adjustment to a team's hitting strategy to maximize the team's projected wins, using the win percentage model found in the following files.

* AtBatOutcomes.ipynb: Notebook that uses the outcome of individual at-bats to model a team's win percentage and implement adjustments to a team's strategy.  Adjusting terminal pitch counts changes the total number of each outcome, and thus the predicted wins of a particular team.

* TeamData.py: Team class code that hold the team's data files and contains most of the underlying functions needed to construct strategy modifications.

* StratMod_PitchSpecific.py:  Python file containing many of the neccessary functions within the AtBatOutcomes Notebook to change a strategy at the level of individual pitches within an at-bat.

* RawPbPtoPitchCount.py: Used to pull out each team's home and away pitch count data for each season of interest. Game data for this project was acquired from [Retrosheet](https://www.retrosheet.org/game.htm) using their raw Play-by-Play data files. These raw files need significant modifications before the data will be usable.

* PythagoreanExpectation.ipynb: Notebook exploring the general problems associated with using Pythagorean Expectation as a win predictor.

* PitchCountHeatmap.ipynb: Notebook to create the heatmaps found in Heatmap folder.

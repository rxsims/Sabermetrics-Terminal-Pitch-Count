# Sabermetrics-Terminal-Pitch-Count

We imagine a scenario where a MLB team manager or hitting coach ask what adjustments can be made to their team's hitting strategy to help improve their chance to win.  Without changing the roster, the strategy cannot easily change by converting some singles into doubles, or doubles into home runs.  Instead, they can only change how aggressive or patient the team is at different pitch counts.  Adjusting these tendencies would manifest in the terminal pitch counts (pitch count when an at-bat ends) of the team over the course of a season.

To provide full context, a hitter's count is the number of balls and strikes the batter has seen in a particular at-bat, written in the form b-s.  Starting at 0-0, the pitch count will change over the course of an at-bat as more pitches are thrown to the batter.  When considering the terminal (pitch) count, we are only considering the final pitch count for that particular batter before the end of an at-bat; The pitch count before the final pitch was thrown in an at-bat.  An important consequence of this is on strikeouts and walks.  If the batter reaches three strikes, resulting in a strikeout, the terminal pitch count would be recorded as having 2 strikes.  Similarly a fourth ball, resulting in a base-on-balls (walk), would be recorded as having a terminal pitch count with 3 balls.  Consequently, the "largest" count that can be reached during an at-bat is 3-2, at which point the terminal pitch count for that at-bat must be 3-2.

Returning to the problem at hand, consider the effect of being more aggressive and swinging at 2-1 pitches more often.  Acquiring this more aggressive strategy would increase the number of balls-in-play at the 2-1 count at the cost of decreasing the number of at-bats reaching 3-1, 2-2, and 3-2 pitch counts.  Conversely, being more patient on 2-1 counts will mean a decrease in the amount of balls-in-play on 2-1 pitches, increasing the number of at-bats reaching counts of 2-2, 3-1, and 3-2.  If these effects are not accounted for, modifying a strategy largely amounts to telling a team to get on base more so they can have more at-bats.

We account for these effects by systematically imposing that the sum of these changes is zero.  In doing so, we are not fundamentally adding more at-bats to a team, but instead adjusting how a team approaches the at-bats they are given.  This interaction between terminal pitch counts means finding an optimal change is somewhat more involved than simply finding the largest coefficient in the linear model.


### General Methodology

Starting with all play-by-play data files from the 2000 to 2009 MLB seasons, we extract the terminal pitch counts for each team's home and away games.  We then check for clusters of different strategies so that separate analysis can be done for each cluster, although only one cluster was found for each of the home and away data.  Finally, we use a Pythagorean Expectation model of the teams' win percentages.

With the model in hand, we can look at any specific team's terminal pitch count data, which describes the team's overall hitting strategy.

<p align="center">
 <img src="https://i.imgur.com/rjQ9wRj.png" width="504" height="288">
</p>

Using matrix transformations, we are then able to simulateously check all single pitch count modified strategies (accounting for the inter-pitch count effects previously mentioned) we can then find which strategy results in the largest improvement of a team.

<p align="center">
 <img src="https://i.imgur.com/GSG3LDe.jpg" width="604" height="127">
</p>

In this output, an aggressive change looks to increase the fraction of at-bats ending on a particular pitch count, while a patient change decreases the fraction. By default we look at a 1% change in a team's strategy, but since the models are linear in each of the pitch counts, one can scale the improvement for a large modification of the strategy.  However, the linear assumptions will eventually break down with large changes, and more accurate models would need to be implemented.  Furthermore, once a large change happens to a team's strategy, opposing teams will attempt to take advantage of these changes.  This type of backreaction on the system is currently not modelled, but would introduce interesting nonlinear effects to the model.


#### Brief explanation of files

StrategyAdjustment.ipynb: Jupyter Notebook that finds the optimal adjustment to a team's hitting strategy to maximize the team's projected wins, using the win percentage model found in the following files.

DataExploration_ModelBuilding.ipynb: Jupyter Notebook containing start-to-end explanation of the data exploration and modeling process used in this problem.

RawPbPtoPitchCount.py: Used to pull out each team's home and away pitch count data for each season of interest. Game data for this project was acquired from [Retrosheet](https://www.retrosheet.org/game.htm) using their raw Play-by-Play data files. These raw files need significant modifications before the data will be usable.

PitchCountHeatmap.ipynb: Jupyter Notebook to create the heatmaps found in Heatmap folder

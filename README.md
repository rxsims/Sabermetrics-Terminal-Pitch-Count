# Sabermetrics-Terminal-Pitch-Count

We imagine a scenario where a MLB team manager or hitting coach ask what adjustments can be made to their team's hitting strategy to help improve their chance to win.  Without changing the roster, the strategy cannot easily change by converting some singles into doubles, or doubles into home runs.  Instead, they can only change how aggressive or patient the team is at different pitch counts.  Adjusting these tendencies would manifest in the terminal pitch counts (pitch count when an at-bat ends) of the team over the course of a season.

As an example, consider the effect of being more aggressive and swinging at 2-1 pitches more often.  Acquiring this more aggressive strategy would increase the number of balls-in-play at the 2-1 count at the cost of decreasing the number of at-bats reaching 3-1, 2-2, and 3-2 pitch counts.  Conversely, being more patient on 2-1 counts will mean a decrease in the amount of balls-in-play on 2-1 pitches, increasing the number of at-bats reaching counts of 2-2, 3-1, and 3-2.

This interaction between terminal pitch counts means finding an optimal change is somewhat more involved than simply finding the largest coefficient in the linear model.  At the same time, if we want to make a cummulative percentage change in the batting strategy of a team, intuitively it makes more sense to apply a series of transformation on one terminal pitch count at a time.

<p align="center">
 <img src="https://i.imgur.com/il5bS8Z.png" width="504" height="288">
 <img src="https://i.imgur.com/IanWOFC.jpg" width="296" height="278">
</p>


#### Brief explanation of files

StrategyAdjustment.ipynb: Jupyter Notebook that finds the optimal adjustment to a team's hitting strategy to maximize the team's projected wins, using the win percentage model found in the following files.

DataExploration_ModelBuilding.ipynb: Jupyter Notebook containing start-to-end explanation of the data exploration and modeling process used in this problem.

RawPbPtoPitchCount.py: Used to pull out each team's home and away pitch count data for each season of interest. Game data for this project was acquired from [Retrosheet](https://www.retrosheet.org/game.htm) using their raw Play-by-Play data files. These raw files need significant modifications before the data will be usable.

PitchCountHeatmap.ipynb: Jupyter Notebook to create the heatmaps found in Heatmap folder

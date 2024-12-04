# 10-01-2024
## Establishing a format
Today I was hoping to spend my time getting the repo up and ideally figuring out a format I can repeat for my engineering journal. A cursory google search did not pull up any templates sadly so I decided on this, a date in H1, a entry title in H2 and a line break at the end of the entry.
```
# Date
## Title
text
---
```

--- 

# 10-08-2024
## Assignment 1
Worked on assignment 1 today. My major sticking points were
- numpy wanting to set the dtype as float32, needed to use `.astype`
- Code snippet from scipy had some things I couldn't understand why they were there. mostly this in the sin function
`2. * np.pi *`
Update 10/15/2024: It turns out you need those contstants since sin is related to pi 

That said everything looks good in audacity. I'm not sure what a 440hz wave should sound like
![img](audacity_clip_assign1.png)

---
--- 

# 10-15-2024
## DFT, FT, Intro
Just did my intro and watched the first two fourier transform videos today, I think I will play with some code on thursday and finish up the videos.
here is the text of my intro(not sure if it is needed)
```
Hi everyone, I'm max. I'm an undergraduate student hopefully graduating in the spring. I have no experience with playing music but do enjoy listening to it at least so maybe that will be helpful lol. I am mostly taking this class because I watched a youtube video about the tools the aphex twin guy used and thought it seemed cool
```
---
--- 

# 10-17-2024
## DFT, FT
Finished watching all the videos , 
wrote a [jupyter notebook](code/messing_with_notes.ipynb) trying to generate all notes per octave starting from a base `fs`  I think I want to play with the FIR filter too if I have time. Also interested in making the different notes sound smoother from one to the other. 
Added some code in the messing with notes to sort of let me use the top of my keyboard to play notes. I need to figure out how to make it play while the key is being held down but it is fun for now

---
--- 

# 10-29-2024
## Starting work on the tone control project
Started work today on the tone control project but ran into problems with the FFT element of it. Spent some time playing with it but think I will need to do more research into scipy.fft to figure out where I am going wrong

---
--- 

# 10-31-2024
## Continuing work on the tone control project ( thinking about term project )
Today I got my fft mostly working, still want to add a sine for some other sort of windowing function to it but thats okay, also got my filters set up so feeling pretty good. Need to spend some time doing research on the filters so I know what I'm doing since right now I am going off a [blog post](https://swharden.com/blog/2020-09-23-signal-filtering-in-python/) and I think it is too abstract.
Got the power ratios down too so now I just need to scale and recombine to output. 

I think for my term project I am interested in building some sort of vocoder or something similar. Not sure what yet but that seems the most interesting to me.

---

--- 

# 11-1&2-2024
## Continuing work on the tone control project 

Using the repo [tone.py](https://github.com/pdx-cs-sound/tone-control/blob/main/tone.py) I am getting closer. I have my filter working using the state and it sounds good. Now trying to figure out scaling. Hard to tell if I am doing it right or not...
Goal is to use fft at each window I am filtering and take values, find min, find x to make all other values,equal to min
use that as volume scale each filtered window

---
--- 

# 11-5-2024
## Continuing work on the tone control project 

tried switching average for mean to get rid of nan
As it turns out I had an error in my code where I was storing array indices instead of actual frequencies


Pre
![img](164814_old.png)
Post
![img](164814_new.png)

It looks like he have more work to do.. I am assuming we want the new one to look like a wall? or at least similar. I can see I am bring the low down alright... Besides the extreme low. But the extreme high might need to be turned up? Or it is possible there are no freqs at that so even my attempts at scaling aren't helping

---
--- 

# 11-17-2024
## Messing with rhosy code and trying to get minilouge esque display to work
playing around a lot with matplotlib in trying to get a display of the wave to the synth is generating to show ala korg minilouge. I love the screen on the minilouge. 

Trials:
using anim function. 
needs to call flush which causes latency. either the input loop needs changing or need to find a better way to do this. 

Think I am leaning towards blitting. Ideally would like an object you can add to your soundevice.output and then display the sound as it is coming.

Seems like threading will be the main problem here. 


---
--- 

# 11-19-2024
## Completely refactored 

Took out all the code from rhosy and dragged it into classes, the classes are lame but now I can start playing with wave generators more.

using a lot of FP here, so taking the 3 base waves I got from misy.py (link) and applying other function to combine/reduce or trying at chords.

right now I am using the ratios described [here](https://music.stackexchange.com/questions/88572/how-are-chord-ratios-developed-exactly) which are 1.000000000 : 1.25992105 : 1.498307077. so I take the function and return a function that takes the same arguments but sums them by this ratio


---

---
Note: each notes can be broken down into fractional notes so we can represent [1,2,1,1]

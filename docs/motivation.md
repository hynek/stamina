# Motivation

:::{tip}
If you prefer video to text, check out [this video](https://www.youtube.com/watch?v=BxikFuvaT1Y) that explains both the motivation for retries as well as the creation of *stamina*.
:::


## The need for retries

Retries are essential for making distributed systems resilient.
Transient errors are unavoidable and can happen for the wildest reasons:

- A network hiccup.
- A remote service being *deployed*.
- A remote service being *overloaded*.
- A remote service *crashed* and is booting back up.
- A cluster manager decided to reshuffle your containers.

And sometimes, one never finds out because a [cosmic ray](https://en.wikipedia.org/wiki/Cosmic_ray) flipped a memory bit.
The bigger the scale, the more likely it is that something will go wrong -- but the chance is never zero.


## The dangers of retries

However, retries are also very dangerous if done naïvely.
Simply repeating an operation until it succeeds can lead to [*cascading failures*](https://en.wikipedia.org/wiki/Cascading_failure) and [*thundering herds*](https://en.wikipedia.org/wiki/Thundering_herd_problem) and ultimately take down your whole system, just because a database had a brief hiccup.

So:

1. You must wait between your retries: this is called a *backoff*.
2. You can't retry simultaneously with all your clients, so you must introduce randomness into your backoff: a *jitter*.
3. You must not retry forever.
   Sometimes, a remote service is down indefinitely, and you must deal with it.

But how long should you back off?
The failure could be a network hiccup, so 100ms?
Maybe an application was just being deployed, so let's do 1 second?
But what if it's a database that's overloaded?
Then maybe 10 seconds?
And so forth.

The answer is:
You do all of those.
You start with a small backoff and increase it exponentially, adding a random jitter.


## *stamina*

That's what *stamina* does by default:
It starts with 100 milliseconds and increases exponentially by 2 until it reaches 5 seconds where it stays until 45 seconds or 10 attempts have passed.
A jitter between 0 and 1 second is added at every step until it reaches the maximum of 5 seconds.

Or, more formally:

% keep in-sync with stamina.retry's docstring
```{math}
min(5.0, 0.1 * 2.0^{attempt - 1} + random(0, 1.0))
```

That means that, by default, the first backoff is no longer than 1.1 seconds, and the last is no longer than 5 seconds.
Note that no jitter is added once the maximum timeout is reached; there should be enough variance in the backoff due to the jitter added underway.

You can [tune all these parameters](stamina.retry) to your liking, but the defaults are a good starting point.

I hope you're now all motivated and ready to jump into our {doc}`tutorial`!


## Supplemental literature

- The [*Exponential Backoff And Jitter*](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) article on the *AWS Architecture Blog* is a good explanation of the basics with pretty graphs.

- [*Addressing Cascading Failures*](https://sre.google/sre-book/addressing-cascading-failures/) is a relevant chapter from Google's [*Site Reliability Engineering* book](https://sre.google/books/).

- [*Resiliency in Distributed Systems*](https://blog.pragmaticengineer.com/resiliency-in-distributed-systems/) takes a broader view and explains how to build resilient systems in general.

- I gave a talk at PyCon US 2017 called [*Solid Snakes or: How to Take 5 Weeks of Vacation*](https://www.youtube.com/watch?v=YVuqeXyvOUc) that addresses the various aspects to take care of to... take five weeks of (uninterrupted!) vacation.
  This one has a stronger focus on Python and working at a smaller scale.

- Finally I recorded a video on my YouTube channel which covers the motivation and use-cases of stamina [*Master Flaky Systems with Retries in Python*](https://www.youtube.com/watch?v=BxikFuvaT1Y).

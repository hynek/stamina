# Motivation

Retries are essential for making distributed systems resilient.
Transient errors are unavoidable and can happen for the wildest reasons -- sometimes, one never finds out.

However, retries are also very dangerous if done naïvely.
Simply repeating an operation until it succeeds can lead to [*cascading failures*](https://en.wikipedia.org/wiki/Cascading_failure) and [*thundering herds*](https://en.wikipedia.org/wiki/Thundering_herd_problem) and ultimately take down your whole system, just because a database had a brief hiccup.

So:

1. You must wait between your retries: this is called a *backoff*.
2. You can't retry simultaneously with all your clients, so you must introduce randomness into your *backoff*: a *jitter*.
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

That's what *stamina* does by default:
It starts with 100ms and increases exponentially by 2 until it reaches 45 seconds or 10 attempts.
A jitter between 0 and 1 second is added at every step.

That means the first backoff is no longer than 1.1 seconds, and the last is no longer than 46 seconds.
You can [tune all these parameters](stamina.retry) to your liking, but the defaults are a good starting point.

---

If you want to learn more:

- The [*Exponential Backoff And Jitter*](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) article on the *AWS Architecture Blog* is a good explanation of the basics with pretty graphs.
- [*Resiliency in Distributed Systems*](https://blog.pragmaticengineer.com/resiliency-in-distributed-systems/) takes a broader view and explains how to build resilient systems in general.
- And finally, I've given a talk at PyCon US 2017 called [*Solid Snakes or: How to Take 5 Weeks of Vacation*](https://www.youtube.com/watch?v=YVuqeXyvOUc) that addresses the various aspects to take care of to... take five weeks of (uninterrupted!) vacation.
  This one has a stronger focus on Python and working at a smaller scale.

import numpy as np
import re
import tensorflow as tf
import time
import util

from gym.envs.atari.atari_env import AtariEnv


class Atari(object):
  def __init__(self, config):
    util.log('Starting %s {frameskip: %s, repeat_action_probability: %s}' %
             (config.game, str(config.frameskip),
              str(config.repeat_action_probability)))

    self.env = Atari.create_env(config)

    if isinstance(config.frameskip, int):
      frameskip = config.frameskip
    else:
      frameskip = config.frameskip[1]

    self.input_frames = config.input_frames
    self.max_noops = config.max_noops / frameskip
    self.render = config.render

    config.num_actions = self.env.action_space.n
    self.episode = 0

  def sample_action(self):
    return self.env.action_space.sample()

  def reset(self):
    """Reset the game and play some random actions"""

    self.start_time = time.time()
    self.episode += 1
    self.steps = 0
    self.score = 0

    frame = self.env.reset()
    if self.render: self.env.render()
    self.frames = [frame]

    for i in range(np.random.randint(self.input_frames, self.max_noops + 1)):
      frame, reward_, done, _ = self.env.step(0)
      if self.render: self.env.render()

      self.steps += 1
      self.frames.append(frame)
      self.score += reward_

      if done: self.reset()

    return self.frames, self.score, done

  def step(self, action):
    frame, reward, done, _ = self.env.step(action)
    if self.render: self.env.render()

    self.steps += 1
    self.frames.append(frame)
    self.score += reward

    return self.frames, reward, done

  def log_episode(self, summary_writer, global_step):
    duration = time.time() - self.start_time
    steps_per_sec = self.steps / duration

    message = 'Episode %d, score %.0f (%d steps, %.2f secs, %.2f steps/sec)'
    util.log(message %
             (self.episode, self.score, self.steps, duration, steps_per_sec))

    summary = tf.Summary()
    summary.value.add(tag='episode/score', simple_value=self.score)
    summary.value.add(tag='episode/steps', simple_value=self.steps)
    summary.value.add(tag='episode/time', simple_value=duration)
    summary.value.add(tag='episode/reward_per_sec', simple_value=self.score / duration)
    summary.value.add(tag='episode/steps_per_sec', simple_value=self.steps / duration)
    summary_writer.add_summary(summary, global_step)

  @classmethod
  def create_env(cls, config):
    game = '_'.join(
        [g.lower() for g in re.findall('[A-Z]?[a-z]+', config.game)])

    return AtariEnv(
        game=game,
        obs_type='image',
        frameskip=config.frameskip,
        repeat_action_probability=config.repeat_action_probability)

  @classmethod
  def num_actions(cls, config):
    return Atari.create_env(config).action_space.n

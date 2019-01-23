# coding=utf-8

import neat
import numpy as np
import gym
import visualize
import wrapped_flappy_bird as game


CONFIG = "./config"
EP_STEP = 300  # maximum episode steps
GENERATION_EP = 5  # evaluate by the minimum of 10-episode rewards
TRAINING = True  # training or testing
CHECKPOINT = 223  # test on this checkpoint
CONTINUE = True  # 接着 CHECKPOINT 继续训练


""" ===================================================================== """
# save_path = 'saved_networks'
env = game.GameState()
# FRAME_PER_ACTION = 10  # 12
# total_steps = 0
# total_score_this_save = 0
# max_real_score_this_save = 0


def eval_genomes(genomes, config):
    p_count = 0
    for genome_id, genome in genomes:   # len(genomes) is pop_size
        print('p_count: %d' % p_count)
        print('============== genome_id: %d ============== : ' % genome_id)
        net = neat.nn.FeedForwardNetwork.create(genome, p.config)
        # net = neat.nn.RecurrentNetwork.create(genome, config)
        ep_r = []
        for ep in range(GENERATION_EP):  # run many episodes for the genome in case it's lucky, 每个基因测试多少条命
            print('======= GENERATION_EP: %d ======= : ' % ep)
            accumulative_r = 0.  # stage longer to get a greater episode reward

            # initial observation
            do_nothing = 0
            observation, r_0, terminal = env.frame_step(do_nothing)

            # for t in range(EP_STEP):    # 每条命测试多久
            while True:
                action_values = net.activate(observation)
                action = np.argmax(action_values)
                observation_, reward, done = env.frame_step(action)
                accumulative_r += reward
                if done:
                    break
                observation = observation_
            ep_r.append(accumulative_r)
        genome.fitness = np.min(ep_r) / float(EP_STEP)  # depends on the minimum episode reward
        print('genome.fitness: %f' % genome.fitness)
        print('')
        p_count += 1


def run_continue(p):
    pop = p

    # recode history
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.StdOutReporter(True))
    pop.add_reporter(neat.Checkpointer(CHECKPOINT))

    pop.run(eval_genomes, 10000 - CHECKPOINT)  # train 10 generations

    # visualize training
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)






def run():
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation, CONFIG)
    pop = neat.Population(config)

    # recode history
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.StdOutReporter(True))
    pop.add_reporter(neat.Checkpointer(5))

    pop.run(eval_genomes, 100)  # train 10 generations

    # visualize training
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)


def evaluation():
    p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-%i' % CHECKPOINT)
    winner = p.run(eval_genomes, 1)  # find the winner in restored population

    # show winner net
    node_names = {-1: 'In0', -2: 'In1', -3: 'In3', -4: 'In4', 0: 'act1', 1: 'act2'}

    # draw graphic
    visualize.draw_net(p.config, winner, True, node_names=node_names)

    net = neat.nn.FeedForwardNetwork.create(winner, p.config)
    # net = neat.nn.RecurrentNetwork.create(winner, p.config)
    while True:
        # initial observation
        do_nothing = 0
        observation, r_0, terminal = env.frame_step(do_nothing)
        while True:
            a = np.argmax(net.activate(observation))
            s, r, done = env.frame_step(a)
            if done:
                break


if __name__ == '__main__':
    if TRAINING and not CONTINUE:
        run()
    elif not TRAINING and not CONTINUE:
        evaluation()
    elif CONTINUE:
        string = "======================= 接着训练 ======================="
        print(string)
        p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-%i' % CHECKPOINT)
        run_continue(p)

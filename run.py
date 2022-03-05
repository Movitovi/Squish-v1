import func
game = func.game()
while game.running:
    game.get_inputs()
    game.move_objects()
    game.update()
game.close()

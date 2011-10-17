from distutils.core import setup
import py2exe
import glob

ver = "0.4"
setup(name='shil-1w1b-entry',
		version=ver,
		description="SHilbert's 1W1B Entry",
		author="Scott Hilbert",
		author_email="1w1b@shilbert.com",
		url="http://www.shilbert.com",
		windows=[{'script':'entry.py',
				  'icon_resources': [(1, "icon.ico")]}],
		data_files=[('.',	  ['README.txt']),
					('music', ['music/static.ogg',
								'music/2001_nointro.ogg',
								'music/bennyhill.ogg']),
					('images', ['images/corner-bottom-left.png',
								'images/corner-bottom-right.png',
								'images/corner-top-left.png',
								'images/corner-top-right.png',
								'images/cover.png',
								'images/glove.png',
								'images/title.png',
								'images/question-bg.png',
								'images/title.png',
								'images/blackout.png',
								'images/gameover-bg.png']),
					('images/intro', ['images/intro/srh.png',
									  'images/intro/1w1b.png',
									  'images/intro/instructions.png',
									  'images/intro/instructions2.png']),
					('images/poo', ['images/poo/poo-0.png',
									'images/poo/poo-1.png',
									'images/poo/poo-2.png',
									'images/poo/poo-3.png']),
					('images/sign', ['images/sign/ready.png',
									 'images/sign/set.png',
									 'images/sign/go.png',
									 'images/sign/press-space.png',
									 'images/sign/choosing.png',
									 'images/sign/sorry.png',
									 'images/sign/great-job.png',
									 'images/sign/pass.png',
									 'images/sign/time-up.png',
									 'images/sign/game-over.png']),
					('misc', ['misc/arial.ttf']),
					('src', ['config.py', 'entry.py', 'README-source.txt']),
					# TODO: A little nicer
					('images/questions', glob.glob("images/questions/*.jpg"))
					]
								
	)
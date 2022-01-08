import { useRouter } from 'next/router';
import { Typography, Box, Container, Grid, IconButton } from '@mui/material';
import Link from '@components/MuiNextLink';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import CardMedia from '@mui/material/CardMedia';
import CenterTitle from '@components/CenterTitle';
import RelatedLinks from '@components/RelatedLinks/RelatedLinks';
import theme from '../../styles/theme';
import Search from '@components/Search';
import TelegramIcon from '@mui/icons-material/Telegram';
import fs from 'fs';
import { useSearch } from '../../utils/SearchContext';

const relatedLinkList = [
  {
    id: 0,
    title: 'Documentation',
    caption: 'Read about how Ergopad Works',
    icon: 'auto_stories',
    href: 'https://github.com/ergo-pad/ergopad/blob/main/docs/README.md',
    background: theme.palette.primary.main,
  },
  {
    id: 1,
    title: 'About',
    caption: 'Learn more about who we are',
    icon: 'emoji_people',
    href: '/about',
    background: theme.palette.secondary.main,
  },
  {
    id: 2,
    title: 'Apply for IDO',
    caption: 'Submit your own project proposal',
    icon: 'chat',
    href: '/apply',
    background: theme.palette.tertiary.main,
  },
];

const Projects = (props) => {
  const router = useRouter();
  const { search } = useSearch();
  const filteredProjects = props.projects?.filter((project) =>
    project.name.includes(search)
  );
  const launchedProjects = filteredProjects?.filter(
    (project) => project.launched
  );
  const upcomingProjects = filteredProjects?.filter(
    (project) => !project.launched
  );

  const projectCard = (project) => {
    return (
      <Grid item xs={12} sm={6} md={4} key={project.project_id}>
        <Card
          sx={{
            display: 'flex',
            height: '100%',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <CardActionArea
            onClick={() =>
              router.push('/projects/' + project.project_id.toString(10))
            }
          >
            <CardMedia
              component="img"
              alt=""
              height="180"
              image={project.banner_img_url}
            />
            <CardContent>
              <Typography gutterBottom variant="h5" component="div">
                {project.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {project.description}
              </Typography>
            </CardContent>
          </CardActionArea>
          <CardActions sx={{ justifyContent: 'right' }}>
            {project.team_telegram_handle ? (
              <Link
                sx={{ display: 'flex', justifyContent: 'center' }}
                href={project.team_telegram_handle}
                aria-label="Telegram"
                title="Telegram"
                rel="noreferrer"
                target="_blank"
              >
                <IconButton aria-label="telegram">
                  <TelegramIcon />
                </IconButton>
              </Link>
            ) : (
              <IconButton aria-label="telegram">
                <TelegramIcon />
              </IconButton>
            )}
          </CardActions>
        </Card>
      </Grid>
    );
  };

  return (
    <>
      <Container sx={{ mb: '3rem' }}>
        <CenterTitle
          title="ErgoPad Projects"
          subtitle="Building the future of the Ergo ecosystem"
          main={true}
        />
        <Box sx={{ display: 'flex', width: '100%', justifyContent: 'center' }}>
          <Search placeholder="Search projects" sx={{}} />
        </Box>
      </Container>
      <Container maxWidth="lg" sx={{}}>
        <Typography variant="h4" sx={{ fontWeight: '800', mb: 4 }}>
          Upcoming
        </Typography>
        <Grid container spacing={3} alignItems="stretch" sx={{ mb: 6 }}>
          {upcomingProjects?.map((project) => projectCard(project))}
        </Grid>
        <Typography variant="h4" sx={{ fontWeight: '800', mb: 4 }}>
          Launched
        </Typography>
        <Grid container spacing={3} alignItems="stretch" sx={{ mb: 6 }}>
          {launchedProjects?.map((project) => projectCard(project))}
        </Grid>
      </Container>
      <RelatedLinks title="Learn More" subtitle="" links={relatedLinkList} />
    </>
  );
};

export const getStaticProps = async () => {
  const data = JSON.parse(
    fs.readFileSync('data/projects.json', { encoding: 'utf-8' })
  );
  return {
    props: { ...data },
  };
};

export default Projects;

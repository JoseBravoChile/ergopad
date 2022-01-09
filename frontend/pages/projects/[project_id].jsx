import { useRouter } from 'next/router';
import Image from 'next/image';
import { Container, Typography, IconButton, Divider, Box } from '@mui/material';
import PageTitle from '@components/PageTitle';
import Link from '@components/MuiNextLink';
import CenterTitle from '@components/CenterTitle';
import RelatedLinks from '@components/RelatedLinks/RelatedLinks';
import TelegramIcon from '@mui/icons-material/Telegram';
import theme from '../../styles/theme';
import fs from 'fs';

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

const Project = (props) => {
  const router = useRouter();
  const { project_id } = router.query;
  const projects = props?.projects.filter(
    (project) => project.project_id == project_id
  );
  const project = projects.length ? projects[0] : null;

  return (
    <>
      {project ? (
        <>
          <Container maxWidth="760px" sx={{ maxWidth: '760px', mx: 'auto' }}>
            <Image
              src={project.banner_img_url}
              alt={project.name}
              layout="responsive"
              height="40%"
              width="80%"
            />
            <Box sx={{ mt: '-5rem' }}>
              <PageTitle title={project.name} />
            </Box>
            <Typography variant="h3">
              Funds raised:{' '}
              {project.funds_raised ? project.funds_raised : 'N/A'}
            </Typography>
            <Divider sx={{ width: '100%', mb: '1.5rem' }} />
            <Typography variant="h4">Description:</Typography>
            <Typography variant="p">{project.description}</Typography>
            <Divider sx={{ width: '100%', mb: '1.5rem' }} />
            <Typography variant="h4">Meet the team:</Typography>
            {/* todo: Add rendering for team */}
            <Typography variant="p">
              Update team description for content in this section.
            </Typography>
            {project.team_telegram_handle ? (
              <Link
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
          </Container>
        </>
      ) : (
        <CenterTitle
          title="Oops..."
          subtitle="Looks like the project you are looking for doesn't exist."
          main={true}
        />
      )}
      <RelatedLinks title="Learn More" subtitle="" links={relatedLinkList} />
    </>
  );
};

export const getStaticPaths = async () => {
  return {
    paths: [],
    fallback: 'blocking',
  };
};

export const getStaticProps = async () => {
  const data = JSON.parse(
    fs.readFileSync('data/projects.json', { encoding: 'utf-8' })
  );
  return {
    props: { ...data },
  };
};

export default Project;
